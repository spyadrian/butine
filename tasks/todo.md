# M2 — tâches

Commandes de vérification communes (depuis `backend/`) :
- Lint : `uv run ruff check . && uv run ruff format --check .`
- Tests : `docker compose up -d db && uv run pytest`

Spec : [docs/SPEC.md](../docs/SPEC.md).

---

## Phase 1 : risque et comptes

### T12 : test du modèle d'embeddings
**Description :** Choisir la bibliothèque (`fastembed` ou `sentence-transformers`), le modèle (bge-small-en-v1.5 ou e5-small-v2), la dimension N et le seuil par défaut. Le script `backend/scripts/match_preview.py` embedde les papiers en base et les prompts de l'utilisateur, puis affiche les meilleurs papiers de chaque prompt avec leur score. L'utilisateur juge la pertinence, et on en déduit le seuil. On mesure la RAM du processus et le temps d'embedding de 3 000 papiers sur CPU. Résultats et choix notés dans DECISIONS.md.

**Critères d'acceptation :**
- [ ] La bibliothèque retenue s'installe et tourne avec la version de Python choisie (3.14, sinon 3.13)
- [ ] Les deux modèles comparés sur les mêmes prompts ; RAM et temps pour 3 000 papiers mesurés
- [ ] Modèle, N et `MATCH_THRESHOLD` par défaut validés par l'utilisateur et notés dans DECISIONS.md

**Vérification :**
- [ ] Lint passe
- [ ] Manuel : `uv run python scripts/match_preview.py prompts.txt` affiche des résultats lisibles

**Dépendances :** aucune (attend les prompts de l'utilisateur)
**Fichiers :** `backend/scripts/match_preview.py`, `backend/pyproject.toml`, `backend/uv.lock`, `docs/DECISIONS.md`
**Taille :** S

### T13 : utilisateurs et commande `set-plan`
**Description :** Modèle `User` (`id` UUID généré par Postgres, `plan` `free|paid` avec contrainte CHECK, `created_at`) + migration. `POST /v1/users` → `201 {"id", "plan"}`. Dépendance FastAPI `current_user` qui lit `X-User-Id` (`401` si absent ou inconnu, `422` si mal formé). Commande `python -m app.cli set-plan <user-id> free|paid`.

**Critères d'acceptation :**
- [ ] `POST /v1/users` crée un utilisateur `free` et renvoie son UUID
- [ ] `set-plan` change le plan ; un id inconnu ou un plan invalide → message clair et code de sortie ≠ 0
- [ ] Aucune route ne permet de changer le plan

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `curl -X POST localhost:8000/v1/users` puis `set-plan`

**Dépendances :** aucune
**Fichiers :** `backend/app/models.py`, `backend/migrations/versions/…`, `backend/app/api/v1/users.py`, `backend/app/main.py`, `backend/app/cli.py`, `backend/tests/test_api_users.py`
**Taille :** M

### T14 : prompts et limite par plan
**Description :** Modèle `Prompt` (`id`, `user_id` FK `ON DELETE CASCADE`, `text`, `created_at`) + migration. `POST /v1/prompts` (texte de 1 à 500 caractères après suppression des espaces autour, `403` au-delà de `PROMPT_LIMITS[plan]`, ligne de l'utilisateur verrouillée pendant le comptage), `GET /v1/prompts` (du plus ancien au plus récent, avec `status`), `DELETE /v1/prompts/{id}`. `status` vaut `pending` tant qu'il n'y a pas d'embedding : toujours le cas avant T16.

**Critères d'acceptation :**
- [ ] `free` : 1 prompt, le 2ᵉ → `403` ; `paid` : 10, le 11ᵉ → `403` ; repasser en `free` garde les prompts mais bloque la création
- [ ] Le prompt d'un autre utilisateur ou un prompt inexistant → `404` (lecture et suppression)
- [ ] Texte vide ou > 500 caractères → `422` ; sans `X-User-Id` → `401`

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : créer, lister et supprimer un prompt avec `curl`

**Dépendances :** T13
**Fichiers :** `backend/app/models.py`, `backend/migrations/versions/…`, `backend/app/api/v1/prompts.py`, `backend/app/main.py`, `backend/tests/test_api_prompts.py`
**Taille :** M

### Checkpoint 1
- [ ] Créer un utilisateur et un prompt avec `curl` ; 2ᵉ prompt refusé en `free`, accepté après `set-plan … paid`
- [ ] Modèle et seuil validés par l'humain (T12)
- [ ] Revue humaine

---

## Phase 2 : embeddings

### T15 : pgvector et colonnes d'embedding
**Description :** Image `pgvector/pgvector:pg18` dans Compose et dans la CI. Dépendance Python `pgvector`. Migration : `CREATE EXTENSION vector`, colonnes `papers.embedding` et `prompts.embedding` en `vector(N)` nullable (N issu de T12).

**Critères d'acceptation :**
- [ ] `alembic upgrade head` passe sur une base vide et sur la base locale existante (données conservées)
- [ ] La CI tourne sur l'image pgvector et reste verte
- [ ] `test_models_match_migrations` passe (modèles et migration alignés)

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `docker compose up -d --build` → `/v1/papers` renvoie toujours les papiers existants

**Dépendances :** T12 (N), T14 (table `prompts`)
**Fichiers :** `docker-compose.yml`, `.github/workflows/ci.yml`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/app/models.py`, `backend/migrations/versions/…`
**Taille :** S

### T16 : embeddings calculés par le worker
**Description :** `services/embeddings.py` : `embed_pending(session, embed, batch_limit)` embedde d'abord tous les prompts sans embedding, puis au plus `EMBED_BATCH_LIMIT` papiers (défaut 2 000), en vecteurs normalisés. Texte d'un papier : `title + "\n\n" + abstract`. L'upsert d'une nouvelle version remet `embedding` à `NULL`. Le worker charge le vrai modèle une fois au démarrage et appelle `embed_pending` après la purge. Modèle téléchargé au build de l'image. Version de Python ajustée si T12 l'exige. `status` d'un prompt : `ready` dès qu'il a un embedding.

**Critères d'acceptation :**
- [ ] Avec un faux embedder : prompts et papiers sans embedding sont remplis, la limite par cycle est respectée, les prompts passent avant les papiers
- [ ] Une nouvelle version d'un papier remet son embedding à `NULL` ; une version plus ancienne n'y touche pas
- [ ] Le worker réel embedde les papiers en base sans erreur, et un prompt créé passe à `ready` au cycle suivant

**Vérification :**
- [ ] Lint + tests passent (aucun vrai modèle chargé dans les tests)
- [ ] Manuel : `docker compose up -d --build`, créer un prompt, `GET /v1/prompts` → `ready` en ≤ 2 min

**Dépendances :** T15
**Fichiers :** `backend/app/services/embeddings.py`, `backend/app/services/fetcher.py`, `backend/app/worker.py`, `backend/app/config.py`, `backend/Dockerfile`, `backend/tests/test_embeddings.py`
**Taille :** M

### T17 : compteurs d'embeddings dans les stats
**Description :** `fetch_cycles` gagne `embedded_papers` et `pending_embeddings` (papiers sans embedding en fin de cycle) + migration. Ils apparaissent dans la ligne de log JSON et dans `/v1/stats`.

**Critères d'acceptation :**
- [ ] Le log et `/v1/stats` donnent les mêmes `embedded_papers` et `pending_embeddings`
- [ ] Avec plus de papiers en attente que `EMBED_BATCH_LIMIT`, `pending_embeddings` reflète le reste

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `docker compose logs worker` puis `curl localhost:8000/v1/stats`

**Dépendances :** T16
**Fichiers :** `backend/app/models.py`, `backend/migrations/versions/…`, `backend/app/worker.py`, `backend/app/api/v1/stats.py`, `backend/tests/test_api_stats.py`
**Taille :** S

### Checkpoint 2
- [ ] `docker compose up` → `pending_embeddings` redescend à 0 et ne grossit plus d'un cycle à l'autre
- [ ] Un nouveau prompt passe à `ready` en ≤ 2 min
- [ ] RAM du worker mesurée, compatible avec un VPS de 4 Go (avec Postgres et l'API)
- [ ] Revue humaine

---

## Phase 3 : feeds

### T18 : feed d'un prompt
**Description :** `services/feeds.py` : requête de matching (similarité `1 − (embedding <=> prompt.embedding) ≥ MATCH_THRESHOLD`, `coalesce(published_at, fetched_at) ≥ prompt.created_at − BACKFILL_DAYS`), triée comme `/v1/papers`. `GET /v1/prompts/{id}/feed?limit&offset` → `PaperOut` + `score`. Prompt `pending` → liste vide ; prompt d'un autre utilisateur → `404`.

**Critères d'acceptation :**
- [ ] Seuil : un papier juste au-dessus est retenu, un papier juste en dessous ne l'est pas (vecteurs choisis à la main)
- [ ] Rattrapage : un papier de 6 jours avant la création du prompt est retenu, un papier de 8 jours ne l'est pas
- [ ] Tri, pagination et `limit` > 200 → `422`, comme `/v1/papers`

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `curl -H "X-User-Id: …" localhost:8000/v1/prompts/1/feed?limit=5` → papiers pertinents

**Dépendances :** T16
**Fichiers :** `backend/app/services/feeds.py`, `backend/app/api/v1/feeds.py`, `backend/app/config.py`, `backend/app/main.py`, `backend/tests/test_api_feeds.py`
**Taille :** M

### T19 : feed global
**Description :** `GET /v1/feed?limit&offset` : l'union des tiroirs des prompts de l'utilisateur. Chaque papier apparaît une fois, avec `score` (le meilleur) et `prompt_ids`. Même tri et même pagination.

**Critères d'acceptation :**
- [ ] Un papier retenu par deux prompts apparaît une fois, avec les deux `prompt_ids` et le meilleur score
- [ ] Les prompts d'un autre utilisateur n'y contribuent pas
- [ ] Utilisateur sans prompt `ready` → liste vide

**Vérification :**
- [ ] Lint + tests passent
- [ ] Manuel : `curl -H "X-User-Id: …" localhost:8000/v1/feed?limit=5`

**Dépendances :** T18
**Fichiers :** `backend/app/services/feeds.py`, `backend/app/api/v1/feeds.py`, `backend/tests/test_api_feeds.py`
**Taille :** S

### Checkpoint final
- [ ] Tous les critères de réussite de docs/SPEC.md remplis
- [ ] `/v1/feed` < 200 ms en local avec ~60 k papiers et 10 prompts (mesuré avec des papiers synthétiques)
- [ ] CI verte
- [ ] Revue humaine avant M3
