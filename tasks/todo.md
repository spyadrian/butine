# M1 — tâches

Commandes de vérification communes (depuis `backend/`) :
- Lint : `uv run ruff check . && uv run ruff format --check .`
- Tests : `docker compose up -d db && uv run pytest`

---

## Phase 1 : fondations

### T1 : squelette backend + Compose + health
**Description :** Créer `backend/` (projet `uv`, FastAPI, SQLAlchemy, psycopg, ruff, pytest), un `Dockerfile`, un `docker-compose.yml` (services `api` et `db` Postgres avec volume), et une route `GET /v1/health` qui exécute `SELECT 1`. Mettre en place la fixture pytest qui se connecte à une base de test Postgres et annule chaque test dans une transaction.

**Critères d'acceptation :**
- [x] `docker compose up` démarre `api` et `db` ; `curl localhost:8000/v1/health` → `{"status": "ok"}`
- [x] Un test appelle `/v1/health` via `TestClient` sur le vrai Postgres et passe
- [x] `/docs` (OpenAPI) liste la route sous `/v1`

**Vérification :**
- [x] Lint + tests passent
- [x] Manuel : `docker compose up --build` puis `curl`

**Dépendances :** aucune
**Fichiers :** `backend/pyproject.toml`, `backend/Dockerfile`, `backend/app/{main,config,db}.py`, `backend/app/api/v1/health.py`, `backend/tests/{conftest,test_health}.py`, `docker-compose.yml`, `.gitignore`
**Taille :** M

### T2 : CI GitHub Actions
**Description :** Workflow sur push/PR : installe `uv`, lance ruff puis pytest avec un service Postgres.

**Critères d'acceptation :**
- [x] Le workflow tourne sur chaque push et PR vers `main`
- [x] Un test volontairement cassé fait échouer la CI (vérifié une fois puis annulé)

**Vérification :**
- [x] Manuel : run vert visible dans l'onglet Actions de `spyadrian/butine`

**Dépendances :** T1
**Fichiers :** `.github/workflows/ci.yml`
**Taille :** XS

### Checkpoint 1
- [x] `docker compose up` OK, `/v1/health` OK
- [x] CI verte
- [x] Revue humaine

---

## Phase 2 : catalogue

### T3 : modèle Source, migration, `sync-sources`
**Description :** Configurer Alembic. Modèle `Source` (id, slug unique, name, url, kind `rss|youtube`, active, etag, last_modified, next_fetch_at, consecutive_failures, last_error). Fichier `sources.yaml` avec quelques sources. Commande `python -m app.cli sync-sources` : ajoute les nouvelles (clé = slug), met à jour nom/url, **désactive** celles retirées du YAML, réactive celles qui y reviennent. Valide le YAML (champs requis, slugs uniques) avant d'écrire.

**Critères d'acceptation :**
- [x] `alembic upgrade head` crée la table sur une base vide
- [x] Ajout, modification, retrait et réapparition d'une source testés
- [x] Un YAML invalide échoue avec un message clair, sans rien modifier en base

**Vérification :**
- [x] Lint + tests passent
- [x] Manuel : `docker compose run --rm api python -m app.cli sync-sources`

**Dépendances :** T1
**Fichiers :** `backend/alembic.ini`, `backend/migrations/`, `backend/app/models.py`, `backend/app/services/catalog.py`, `backend/app/cli.py`, `backend/sources.yaml`, `backend/tests/test_catalog.py`
**Taille :** M

### T4 : `GET /v1/sources`
**Description :** Liste des sources actives (slug, name, url, kind). Schéma Pydantic de réponse séparé du modèle SQLAlchemy (évite d'exposer etag, erreurs, etc.).

**Critères d'acceptation :**
- [x] Ne renvoie que les sources actives, triées par nom
- [x] Les champs internes (etag, last_error…) n'apparaissent pas

**Vérification :**
- [x] Lint + tests passent
- [x] Manuel : `curl localhost:8000/v1/sources`

**Dépendances :** T3
**Fichiers :** `backend/app/api/v1/sources.py`, `backend/app/main.py`, `backend/tests/test_api_sources.py`
**Taille :** S

### T5 : catalogue arXiv + bioRxiv
**Description :** Recentrage sur les papiers scientifiques. Remplacer les kinds `rss|youtube` par `arxiv|biorxiv` (le kind choisit l'extracteur en T6). `sources.yaml` : une source par archive arXiv (`https://rss.arxiv.org/rss/<archive>`, ~20 archives : `cs`, `math`, `physics`, `astro-ph`, `cond-mat`, `quant-ph`, `stat`, `eess`, `q-bio`…) + bioRxiv. Trouver l'URL du flux bioRxiv qui marche (les anciennes `connect.biorxiv.org/biorxiv_xml/…` renvoient 404). Les anciennes sources (presse, YouTube) sont retirées du YAML, donc désactivées par `sync-sources`.

**Critères d'acceptation :**
- [ ] `kind` hors `arxiv|biorxiv` → YAML refusé avec un message clair
- [ ] Toutes les URLs du YAML répondent 200 avec du XML (vérifié une fois à la main)
- [ ] Après `sync-sources`, `/v1/sources` ne liste que les sources arXiv et bioRxiv

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `sync-sources` puis `curl localhost:8000/v1/sources`

**Dépendances :** T3
**Fichiers :** `backend/app/services/catalog.py`, `backend/sources.yaml`, `backend/tests/test_catalog.py`
**Taille :** S

### Checkpoint 2
- [ ] Modifier `sources.yaml` → `sync-sources` → visible dans `/v1/sources`
- [ ] Revue humaine

---

## Phase 3 : récupération

### T6 : parsing des flux
**Description :** Fonctions pures `parse_feed(kind, content: bytes) -> list[PaperEntry]` basées sur `feedparser`, un extracteur par kind. `PaperEntry` : `external_id` (`arxiv:2410.12345` / `doi:10.1101/…`, **sans** la version), `version`, title, authors (liste), abstract **complet** nettoyé du HTML (pas tronqué), categories (liste), link, published_at. Entrée sans identifiant → ignorée.

**Critères d'acceptation :**
- [ ] Fixtures réelles arXiv et bioRxiv (RSS 1.0 / RDF) parsées correctement
- [ ] La version est séparée de l'identifiant (`2410.12345v2` → `arxiv:2410.12345`, version 2)
- [ ] Entrée sans identifiant → ignorée ; flux mal formé → liste vide ou erreur explicite, jamais de crash non géré

**Vérification :**
- [ ] Lint + tests passent

**Dépendances :** T5
**Fichiers :** `backend/app/services/feeds.py`, `backend/tests/fixtures/*.xml`, `backend/tests/test_feeds.py`
**Taille :** M

### T7 : Paper, cycle du worker, conteneur worker
**Description :** Modèle `Paper` (external_id **unique**, source_id = première source, version, title, authors, abstract, categories, link, published_at, fetched_at) + migration. `run_cycle(session, client)` : pour chaque source active dont `next_fetch_at <= now`, GET avec `If-None-Match`/`If-Modified-Since`, 304 → rien, 200 → parse + upsert par `external_id` : nouveau papier inséré, version plus récente → mise à jour, sinon rien. Stocke etag/last_modified, `next_fetch_at = now + 30 min`. `worker.py` boucle : `run_cycle` puis dort 60 s. Service `worker` dans Compose.

**Critères d'acceptation :**
- [ ] Deux cycles sur le même flux → aucun doublon
- [ ] Un papier présent dans deux archives → une seule ligne
- [ ] Une `v2` met à jour la ligne de la `v1` ; une `v1` arrivée après la `v2` ne l'écrase pas
- [ ] Les en-têtes conditionnels sont envoyés, un 304 n'insère rien
- [ ] Une source pas encore due n'est pas interrogée

**Vérification :**
- [ ] Lint + tests passent (httpx `MockTransport` servant les fixtures, aucun réseau)
- [ ] Manuel : `docker compose up` → papiers en base après une minute

**Dépendances :** T5, T6
**Fichiers :** `backend/app/models.py`, `backend/migrations/versions/…`, `backend/app/services/fetcher.py`, `backend/app/worker.py`, `docker-compose.yml`, `backend/tests/test_fetcher.py`
**Taille :** M

### T8 : `GET /v1/papers`
**Description :** Papiers du plus récent au plus ancien, avec le nom de la source. Pagination `limit` (défaut 50, max 200) + `offset`, filtre optionnel `source` (slug).

**Critères d'acceptation :**
- [ ] Tri par date décroissante, pagination respectée, `limit` > 200 refusé (422)
- [ ] Filtre `source` fonctionne ; slug inconnu → liste vide

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `curl 'localhost:8000/v1/papers?limit=5'`

**Dépendances :** T7
**Fichiers :** `backend/app/api/v1/papers.py`, `backend/app/main.py`, `backend/tests/test_api_papers.py`
**Taille :** S

### Checkpoint 3
- [ ] `docker compose up` → vrais papiers dans `/v1/papers`
- [ ] Pas de doublons après plusieurs cycles
- [ ] Revue humaine

---

## Phase 4 : robustesse et observabilité

### T9 : backoff et désactivation
**Description :** Sur erreur (réseau, HTTP ≥ 400, flux illisible) : `consecutive_failures += 1`, `last_error` conservé, `next_fetch_at = now + 30 min × 2^(échecs−1)` plafonné (ex. 24 h). À 10 échecs : `active = false`. Un succès remet le compteur à zéro. Une source en erreur n'interrompt pas le cycle des autres.

**Critères d'acceptation :**
- [ ] Délais de backoff croissants et plafonnés (testés)
- [ ] 10ᵉ échec → source désactivée, erreur conservée
- [ ] Une source en erreur n'empêche pas les autres d'être récupérées

**Vérification :**
- [ ] Lint + tests passent

**Dépendances :** T7
**Fichiers :** `backend/app/services/fetcher.py`, `backend/tests/test_fetcher.py`
**Taille :** S

### T10 : purge
**Description :** Supprimer les papiers dont `fetched_at` a plus de `PAPER_RETENTION_DAYS` jours (défaut 30), à chaque cycle du worker.

**Critères d'acceptation :**
- [ ] Papiers plus vieux que la rétention supprimés, les autres conservés
- [ ] Rétention réglable par variable d'environnement

**Vérification :**
- [ ] Lint + tests passent

**Dépendances :** T7
**Fichiers :** `backend/app/services/purge.py`, `backend/app/worker.py`, `backend/app/config.py`, `backend/tests/test_purge.py`
**Taille :** XS

### T11 : log de cycle + `GET /v1/stats`
**Description :** Table `fetch_cycles` (started_at, duration_ms, feeds_polled, new_papers, updated_papers, errors, purged) + migration. Chaque cycle écrit une ligne en base et une ligne de log JSON sur stdout. `GET /v1/stats` renvoie le dernier cycle + le nombre de sources actives/désactivées et de papiers. (Le compteur « en attente d'embedding » arrive en M2 avec les embeddings.)

**Critères d'acceptation :**
- [ ] Une ligne de log JSON par cycle avec durée, flux interrogés, nouveaux papiers, erreurs
- [ ] `/v1/stats` renvoie les mêmes chiffres que le dernier log
- [ ] `/v1/stats` sans aucun cycle → réponse valide (pas d'erreur 500)

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `docker compose logs worker` et `curl localhost:8000/v1/stats`

**Dépendances :** T9, T10
**Fichiers :** `backend/app/models.py`, `backend/migrations/versions/…`, `backend/app/worker.py`, `backend/app/api/v1/stats.py`, `backend/tests/test_api_stats.py`
**Taille :** M

### Checkpoint final
- [ ] Toutes les briques de M1 (DECISIONS.md) livrées
- [ ] CI verte
- [ ] Revue humaine avant M2
