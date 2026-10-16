# Plan d'implémentation : jalon M1 — catalogue, worker, API

## Vue d'ensemble
M1 livre le socle backend : le catalogue `backend/sources.yaml` synchronisé en base, un worker qui récupère les flux RSS/Atom toutes les 30 min (requêtes conditionnelles, dédoublonnage, backoff, purge), une API `/v1` en lecture (sources, articles, stats), le tout dans Docker Compose (api, worker, db) avec une CI GitHub Actions (ruff + pytest sur vrai Postgres).
Référence : [docs/DECISIONS.md](../docs/DECISIONS.md). Ce plan n'y ajoute que des choix d'implémentation.

## Choix d'implémentation (nouveaux, à valider)
| Choix | Raison |
|---|---|
| `uv` pour les dépendances (`pyproject.toml` + `uv.lock`) | Déjà installé ; un seul outil pour venv, lock et exécution (`uv run pytest`). |
| SQLAlchemy **synchrone** + `psycopg` 3 | Plus simple à apprendre que l'async ; FastAPI exécute les routes `def` dans un pool de threads, suffisant ici. |
| `feedparser` pour lire les flux | Gère RSS 0.9x/1.0/2.0, Atom et les flux mal formés ; écrire son parseur serait long et fragile. |
| `httpx` pour télécharger | Client HTTP moderne ; son `MockTransport` permet de tester le worker sans réseau. À revoir en T6 : Starlette pousse désormais vers `httpx2` (déjà utilisé pour le `TestClient`). |
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
    api/v1/   (health, sources, articles, stats)
    services/ (catalog, feeds, fetcher, purge)
  tests/
    fixtures/ (rss2.xml, atom.xml, youtube.xml, broken.xml)
docker-compose.yml
.github/workflows/ci.yml
```

## Graphe de dépendances
```
T1 squelette (FastAPI + Postgres + Compose + pytest)
 ├── T2 CI
 └── T3 modèle Source + Alembic + sync-sources
      └── T4 GET /v1/sources
           └── T5 parsing des flux (fonction pure)
                └── T6 Article + cycle du worker + conteneur worker
                     ├── T7 GET /v1/articles
                     ├── T8 erreurs : backoff + désactivation
                     ├── T9 purge 30 jours
                     └── T10 log de cycle + GET /v1/stats
```
T5 ne dépend techniquement que de T1 (fonction pure) : il peut être fait en parallèle de T3/T4.
T7, T8, T9 sont indépendants entre eux une fois T6 fait. T10 vient en dernier car il compte les erreurs (T8) et les purges (T9).

## Liste des tâches
Détail (critères, vérifications, fichiers) dans [todo.md](todo.md).

### Phase 1 : fondations
- [x] T1 : squelette backend + Compose + `GET /v1/health` testé sur Postgres
- [x] T2 : CI GitHub Actions (ruff + pytest)

### Checkpoint 1
- [ ] `docker compose up` démarre api + db, `/v1/health` répond `ok`
- [ ] CI verte sur GitHub

### Phase 2 : catalogue
- [ ] T3 : modèle `Source`, première migration, commande `sync-sources`
- [ ] T4 : `GET /v1/sources`

### Checkpoint 2
- [ ] Modifier `sources.yaml` + `sync-sources` → changement visible dans `/v1/sources`

### Phase 3 : récupération
- [ ] T5 : parsing des flux en entrées normalisées
- [ ] T6 : modèle `Article`, cycle du worker (conditionnel + dédoublonnage), conteneur `worker`
- [ ] T7 : `GET /v1/articles`

### Checkpoint 3 (le flux principal marche de bout en bout)
- [ ] `docker compose up` → de vrais articles apparaissent dans `/v1/articles` en quelques minutes
- [ ] Relancer un cycle ne crée aucun doublon

### Phase 4 : robustesse et observabilité
- [ ] T8 : backoff progressif + désactivation après 10 échecs
- [ ] T9 : purge des articles > 30 jours
- [ ] T10 : ligne de log par cycle + `GET /v1/stats`

### Checkpoint final
- [ ] Tous les critères de M1 (DECISIONS.md) remplis
- [ ] CI verte, revue humaine

## Risques et mitigations
| Risque | Impact | Mitigation |
|---|---|---|
| Une dépendance pas encore compatible Python 3.14 | Moyen | Vérifié dès T1 (`uv sync`) ; sinon image `python:3.13-slim`, déjà prévu en M2. |
| Flux réels mal formés ou sans `guid` | Moyen | Fixtures dédiées (`broken.xml`, entrée sans guid) en T5 ; repli sur le lien. |
| Tests qui polluent la base entre eux | Moyen | Base de test séparée, chaque test dans une transaction annulée (T1). |
| Serveurs qui ignorent `ETag`/`If-Modified-Since` | Faible | Le dédoublonnage par contrainte unique protège quand même ; seul le coût réseau augmente. |
| Interprétation de « cycle » pour la règle Celery | Faible | Cycle = un réveil du worker (toutes les minutes) ; durée comparée à l'intervalle de réveil. |

## Questions tranchées (2026-10-15)
1. `uv` validé.
2. `sources.yaml` : 3–5 exemples variés (RSS, Atom, YouTube).
3. « Cycle » pour la règle Celery = un réveil du worker (toutes les minutes).
