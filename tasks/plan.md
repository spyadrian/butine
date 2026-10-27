# Plan d'implémentation : jalon M1 — catalogue, worker, API

## Vue d'ensemble
M1 livre le socle backend : le catalogue `backend/sources.yaml` (tout arXiv + bioRxiv) synchronisé en base, un worker qui récupère les flux RSS toutes les 30 min (requêtes conditionnelles, dédoublonnage des papiers, backoff, purge), une API `/v1` en lecture (sources, papiers, stats), le tout dans Docker Compose (api, worker, db) avec une CI GitHub Actions (ruff + pytest sur vrai Postgres).
Référence : [docs/DECISIONS.md](../docs/DECISIONS.md). Ce plan n'y ajoute que des choix d'implémentation.

## Choix d'implémentation (nouveaux, à valider)
| Choix | Raison |
|---|---|
| `uv` pour les dépendances (`pyproject.toml` + `uv.lock`) | Déjà installé ; un seul outil pour venv, lock et exécution (`uv run pytest`). |
| SQLAlchemy **synchrone** + `psycopg` 3 | Plus simple à apprendre que l'async ; FastAPI exécute les routes `def` dans un pool de threads, suffisant ici. |
| `feedparser` pour lire les flux | Gère RSS 0.9x/1.0/2.0, Atom et les flux mal formés ; écrire son parseur serait long et fragile. |
| `httpx` pour télécharger | Client HTTP moderne ; son `MockTransport` permet de tester le worker sans réseau. À revoir en T7 : Starlette pousse désormais vers `httpx2` (déjà utilisé pour le `TestClient`). |
| Parsing par source (`arxiv`, `biorxiv`) au-dessus de `feedparser` | Chaque source a son format d'identifiant (arXiv id vs DOI) et de version ; le `kind` de la source choisit l'extracteur. |
| Colonne `next_fetch_at` par source | Un seul champ gère à la fois l'intervalle de 30 min et le backoff. Le worker se réveille chaque minute et traite les sources « dues ». |
| Table `fetch_cycles` (une ligne par cycle) | Le worker et l'API sont deux processus : `GET /v1/stats` lit la base au lieu de partager de la mémoire. |
| Config par variables d'environnement (`os.environ` + valeurs par défaut) | Trois ou quatre réglages ; pas besoin de `pydantic-settings` pour l'instant. |

Structure visée (respecte « `api/v1/` + `services/` » des décisions) :
```
backend/
  pyproject.toml  uv.lock  Dockerfile  alembic.ini  sources.yaml
  migrations/
  app/
    main.py  config.py  db.py  models.py  cli.py  worker.py
    api/v1/   (health, sources, papers, stats)
    services/ (catalog, feeds, fetcher, purge)
  tests/
    fixtures/ (arxiv.xml, biorxiv.xml, broken.xml)
docker-compose.yml
.github/workflows/ci.yml
```

## Graphe de dépendances
```
T1 squelette (FastAPI + Postgres + Compose + pytest)
 ├── T2 CI
 └── T3 modèle Source + Alembic + sync-sources
      ├── T4 GET /v1/sources
      └── T5 catalogue arXiv + bioRxiv (kinds arxiv | biorxiv)
           └── T6 parsing des flux par source (fonctions pures)
                └── T7 Paper + cycle du worker + conteneur worker
                     ├── T8 GET /v1/papers
                     ├── T9 erreurs : backoff + désactivation
                     ├── T10 purge 30 jours
                     └── T11 log de cycle + GET /v1/stats
```
T6 dépend de T5 car le `kind` de la source choisit l'extracteur.
T8, T9, T10 sont indépendants entre eux une fois T7 fait. T11 vient en dernier car il compte les erreurs (T9) et les purges (T10).

_Révisé le 2026-10-27 : recentrage sur les papiers scientifiques. Ajout de T5 (catalogue) ; `Article` devient `Paper` ; les anciennes T5–T10 deviennent T6–T11._

## Liste des tâches
Détail (critères, vérifications, fichiers) dans [todo.md](todo.md).

### Phase 1 : fondations
- [x] T1 : squelette backend + Compose + `GET /v1/health` testé sur Postgres
- [x] T2 : CI GitHub Actions (ruff + pytest)

### Checkpoint 1
- [x] `docker compose up` démarre api + db, `/v1/health` répond `ok`
- [x] CI verte sur GitHub

### Phase 2 : catalogue
- [x] T3 : modèle `Source`, première migration, commande `sync-sources`
- [x] T4 : `GET /v1/sources`
- [ ] T5 : catalogue arXiv + bioRxiv, retrait de YouTube

### Checkpoint 2
- [ ] Modifier `sources.yaml` + `sync-sources` → changement visible dans `/v1/sources`

### Phase 3 : récupération
- [ ] T6 : parsing des flux arXiv et bioRxiv en papiers normalisés
- [ ] T7 : modèle `Paper`, cycle du worker (conditionnel + dédoublonnage + versions), conteneur `worker`
- [ ] T8 : `GET /v1/papers`

### Checkpoint 3 (le flux principal marche de bout en bout)
- [ ] `docker compose up` → de vrais papiers apparaissent dans `/v1/papers` en quelques minutes
- [ ] Relancer un cycle ne crée aucun doublon ; un papier présent dans deux archives n'apparaît qu'une fois

### Phase 4 : robustesse et observabilité
- [ ] T9 : backoff progressif + désactivation après 10 échecs
- [ ] T10 : purge des papiers > 30 jours
- [ ] T11 : ligne de log par cycle + `GET /v1/stats`

### Checkpoint final
- [ ] Tous les critères de M1 (DECISIONS.md) remplis
- [ ] CI verte, revue humaine

## Risques et mitigations
| Risque | Impact | Mitigation |
|---|---|---|
| Une dépendance pas encore compatible Python 3.14 | Moyen | Vérifié dès T1 (`uv sync`) ; sinon image `python:3.13-slim`, déjà prévu en M2. |
| Flux réels mal formés ou sans identifiant | Moyen | Fixtures dédiées (`broken.xml`, entrée sans identifiant) en T6 ; une entrée sans identifiant est ignorée. |
| URL du flux bioRxiv introuvable (anciennes URLs en 404) | Moyen | Recherchée en T5 ; à défaut, M1 part avec arXiv seul et bioRxiv suit dès que l'URL est trouvée. |
| Tests qui polluent la base entre eux | Moyen | Base de test séparée, chaque test dans une transaction annulée (T1). |
| Volume (~3 000 papiers un jour de semaine) | Faible | Insertion par lots ; à surveiller avec la règle Celery (T11). |
| Serveurs qui ignorent `ETag`/`If-Modified-Since` | Faible | Le dédoublonnage par `external_id` unique protège quand même ; seul le coût réseau augmente. |
| Interprétation de « cycle » pour la règle Celery | Faible | Cycle = un réveil du worker (toutes les minutes) ; durée comparée à l'intervalle de réveil. |

## Questions tranchées (2026-10-15)
1. `uv` validé.
2. `sources.yaml` : 3–5 exemples variés (RSS, Atom, YouTube). _Remplacé le 2026-10-27 : tout arXiv (une source par archive) + bioRxiv._
3. « Cycle » pour la règle Celery = un réveil du worker (toutes les minutes).
