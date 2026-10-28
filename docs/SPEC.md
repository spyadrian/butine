# Spec : jalon M2 — utilisateurs, prompts, matching, feeds

Référence : [DECISIONS.md](DECISIONS.md). Cette spec n'y ajoute que ce qui est nécessaire pour coder M2 ; en cas de conflit, la décision la plus récente l'emporte et l'autre document est mis à jour.

## Objectif
Un utilisateur écrit en anglais ce qu'il cherche (« prompt »). Chaque prompt a son **tiroir** : les papiers arXiv/bioRxiv dont l'embedding est assez proche de celui du prompt. Un **feed global** regroupe tous ses tiroirs. Le nombre de prompts dépend du plan : 1 en `free`, 10 en `paid`.

Utilisateur visé : un chercheur ou un étudiant qui veut voir passer les nouveaux papiers de son sujet sans parcourir des milliers de titres par jour (~3 000 papiers arXiv par jour).

M2 est **backend uniquement** : l'app Flutter (M3) consommera ces routes.

**Hors périmètre M2 :** authentification, compte anonyme, paiement et webhook, gel des prompts au retour au gratuit, modification d'un prompt, suppression de compte, 👍/👎, résumés IA, notifications.

## Carte des capacités

| Module | Rôle | Dépend de |
|---|---|---|
| `accounts` | Table `users` avec le plan, sans authentification | — |
| `prompts` | Créer, lister et supprimer un prompt, avec la limite par plan | `accounts` |
| `embeddings` | pgvector, modèle local, embeddings des papiers et des prompts calculés par le worker | `prompts` |
| `feeds` | Matching par seuil, rattrapage sur 7 jours, feed par prompt et feed global | `embeddings`, `prompts` |

Ordre de construction : `accounts` → `prompts` → `embeddings` → `feeds`.

### `accounts`
- Table `users` : `id` UUID (généré par Postgres, `gen_random_uuid()`), `plan` `free|paid` (défaut `free`, contrainte CHECK), `created_at`.
- `POST /v1/users` → `201 {"id": "<uuid>", "plan": "free"}`.
- Les routes utilisateur lisent l'en-tête `X-User-Id`. S'il manque ou que l'utilisateur est inconnu → `401`. Un UUID mal formé → `422`.
- **Aucune route ne change le plan** : en M2, ça passe par `python -m app.cli set-plan <user-id> free|paid`. Le webhook RevenueCat le remplacera.
- *Raison :* un UUID ne se devine pas et deviendra le jeton du compte anonyme. Sans authentification, une route de changement de plan permettrait à n'importe qui de passer en payant.

### `prompts`
- Table `prompts` : `id` entier, `user_id` (FK `users`, `ON DELETE CASCADE`), `text` (1 à 500 caractères après suppression des espaces autour), `embedding` vector nullable, `created_at`.
- `POST /v1/prompts {"text": "..."}` → `201` avec le prompt créé (`status: "pending"`).
  - Limite atteinte → `403` avec un message qui indique la limite du plan. Limites dans le code : `PROMPT_LIMITS = {"free": 1, "paid": 10}`.
  - Deux créations simultanées ne doivent pas dépasser la limite : la ligne de l'utilisateur est verrouillée (`SELECT … FOR UPDATE`) pendant le comptage.
- `GET /v1/prompts` → les prompts de l'utilisateur, du plus ancien au plus récent : `id`, `text`, `created_at`, `status` (`pending` tant que l'embedding n'est pas calculé, puis `ready`).
- `DELETE /v1/prompts/{id}` → `204`. Le prompt d'un autre utilisateur, ou un prompt inexistant → `404`.
- Pas de modification : l'app fera supprimer + recréer.
- Un passage de `paid` à `free` ne touche pas aux prompts existants. Il bloque seulement la création de nouveaux prompts tant que l'utilisateur est au-dessus de la limite. Le gel arrive avec le paiement.

### `embeddings`
- Postgres passe à l'image `pgvector/pgvector:pg18` (Compose et CI), avec l'extension `vector` créée par une migration.
- Colonnes `papers.embedding` et `prompts.embedding` : `vector(N)` nullable, N fixé par le modèle choisi (probablement 384).
- Texte embeddé : `title + "\n\n" + abstract` pour un papier, `text` pour un prompt. Les vecteurs sont **normalisés**, et la similarité vaut `1 − distance cosinus` (`<=>`).
- **Seul le worker charge le modèle.** À chaque cycle, après la récupération et la purge, il calcule :
  1. les embeddings des prompts qui n'en ont pas encore (tous) ;
  2. ceux des papiers qui n'en ont pas, par lots, avec au plus `EMBED_BATCH_LIMIT` papiers par cycle (défaut 2 000) pour que la durée d'un cycle reste bornée.
- Quand un papier reçoit une nouvelle version (upsert), son `embedding` repasse à `NULL` pour être recalculé.
- La fonction d'embedding est passée en paramètre (`embed: Callable[[list[str]], list[list[float]]]`) : les tests utilisent un faux embedder déterministe, et seul le worker réel charge le modèle.
- `fetch_cycles` et le log JSON gagnent `embedded_papers` et `pending_embeddings` (papiers encore sans embedding en fin de cycle). `/v1/stats` les expose.
- **Première tâche : un test du modèle**, qui fixe le modèle, la bibliothèque, N et le seuil par défaut. Résultats notés dans DECISIONS.md :
  - bibliothèque : `sentence-transformers` (torch) ou `fastembed` (ONNX, sans torch, plus léger) ; vérifier la compatibilité avec Python 3.14 (sinon, image en 3.13) ;
  - modèle : bge-small-en-v1.5 contre e5-small-v2 sur 10 à 20 vrais prompts de l'utilisateur et les papiers en base ;
  - mesures : RAM du worker, temps d'embedding de 3 000 papiers sur CPU, et seuil qui sépare au mieux les bons papiers du bruit.

### `feeds`
- Un papier est dans le tiroir du prompt P si :
  - `similarité(papier, P) ≥ MATCH_THRESHOLD` (variable d'environnement, défaut fixé par le test du modèle) ;
  - `coalesce(published_at, fetched_at) ≥ P.created_at − BACKFILL_DAYS` (défaut 7 jours).
- **Calcul à la volée en SQL**, sans table de correspondances. Un changement de seuil s'applique tout de suite. Pas d'index ANN en M2 : une lecture exacte de ~60 k papiers suffit.
- `GET /v1/prompts/{id}/feed?limit&offset` → papiers au format `PaperOut` + `score`. Prompt d'un autre utilisateur → `404`. Prompt encore `pending` → liste vide.
- `GET /v1/feed?limit&offset` → l'union des tiroirs des prompts de l'utilisateur. Chaque papier n'y apparaît qu'une fois, avec `score` (le meilleur) et `prompt_ids` (les prompts qui le retiennent).
- Tri et pagination identiques à `/v1/papers` : date de publication décroissante (`NULL` à la fin), puis `id` décroissant ; `limit` défaut 50, max 200.
- *Raison du calcul à la volée :* moins de code (pas de rattrapage, de recalcul ni de purge de correspondances). À remplacer par une table de correspondances si la lecture d'un feed dépasse ~200 ms, ou quand il faudra du « non lu » ou des notifications.

## Tech Stack
Celui de M1 (Python 3.14, FastAPI, SQLAlchemy 2 synchrone, psycopg 3, Alembic, PostgreSQL 18, httpx2, feedparser, pytest, ruff, uv, Docker Compose, GitHub Actions), plus :
- `pgvector` : l'extension Postgres et le paquet Python pour le type SQLAlchemy `Vector`.
- Une bibliothèque d'embeddings choisie lors du test du modèle (`fastembed` ou `sentence-transformers`).

## Commands
Depuis `backend/` :
```
Lint      : uv run ruff check . && uv run ruff format --check .
Tests     : docker compose up -d db && uv run pytest
Migration : uv run alembic revision --autogenerate -m "<message>"
Plan      : docker compose run --rm api python -m app.cli set-plan <user-id> paid
Stack     : docker compose up -d --build   (depuis la racine)
```

## Project Structure
Ajouts à la structure de M1 :
```
backend/app/
  api/v1/users.py      POST /v1/users + dépendance current_user (X-User-Id)
  api/v1/prompts.py    CRUD des prompts + limite
  api/v1/feeds.py      GET /v1/prompts/{id}/feed, GET /v1/feed
  services/embeddings.py   chargement du modèle + embed_pending(session, embed)
  services/feeds.py        requête de matching partagée par les deux feeds
backend/tests/
  test_api_users.py  test_api_prompts.py  test_api_feeds.py  test_embeddings.py
```

## Code Style
Comme M1 : identifiants, commentaires et commits en anglais ; docs en français. Routes `def` (synchrones) avec un schéma Pydantic de sortie séparé du modèle SQLAlchemy ; logique réutilisée dans `services/` ; un commentaire seulement pour le *pourquoi*.
```python
@router.post("/prompts", status_code=201)
def create_prompt(
    body: PromptIn,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)],
) -> PromptOut:
    # Row lock: two concurrent requests must not both pass the limit check.
    session.execute(select(User).where(User.id == user.id).with_for_update())
    count = session.scalar(select(func.count()).where(Prompt.user_id == user.id))
    if count >= PROMPT_LIMITS[user.plan]:
        raise HTTPException(403, f"{user.plan} plan allows {PROMPT_LIMITS[user.plan]} prompts")
    ...
```

## Testing Strategy
- pytest sur un vrai Postgres (avec pgvector), avec rollback après chaque test, comme en M1. Aucun appel réseau.
- **Les tests ne chargent jamais le vrai modèle.** Un faux embedder renvoie des vecteurs choisis à la main (ex. axes orthogonaux) pour contrôler exactement les similarités.
- À couvrir en priorité :
  - limite de prompts par plan (free 1, paid 10, `paid` → `free` qui bloque la création) ;
  - isolation entre utilisateurs (404 sur le prompt d'un autre) ;
  - seuil (juste au-dessus et juste en dessous) ;
  - fenêtre de rattrapage (papier à 6 et à 8 jours) ;
  - dédoublonnage du feed global ;
  - recalcul de l'embedding après une nouvelle version ;
  - `EMBED_BATCH_LIMIT` respecté ;
  - `pending_embeddings` dans `/v1/stats`.
- Le vrai modèle est vérifié à la main lors du test du modèle, puis par `docker compose up` (checkpoint).

## Boundaries
- **Always :** une branche et une PR par tâche, test qui échoue d'abord, lint et tests avant chaque commit, une migration Alembic pour tout changement de schéma, une décision nouvelle reportée dans DECISIONS.md.
- **Ask first :** toute dépendance autre que `pgvector` et la bibliothèque d'embeddings retenue ; changer un contrat `/v1` existant ; le choix final du modèle et du seuil (présentés avec les mesures du test du modèle) ; committer les prompts de test de l'utilisateur.
- **Never :** une route qui change le plan ; une API d'embeddings externe ou payante ; charger le modèle dans l'API ; pousser ou merger sur `main` ; mettre des task IDs dans les commits, PR ou branches.

## Success Criteria
1. `POST /v1/users` puis `POST /v1/prompts` fonctionnent. Un 2ᵉ prompt en `free` → `403`. Après `set-plan … paid`, 10 prompts sont acceptés et le 11ᵉ est refusé.
2. Sur `docker compose up` avec la vraie base, un nouveau prompt passe à `ready` en moins de 2 cycles (≤ 2 min), et son feed contient des papiers pertinents des 7 derniers jours.
3. Un nouveau papier récupéré par le worker apparaît dans les feeds concernés au plus tard au cycle suivant.
4. `pending_embeddings` redescend à 0 après le rattrapage initial et ne grossit pas d'un cycle à l'autre en régime normal. S'il grossit, on applique la règle Celery de DECISIONS.md.
5. `GET /v1/feed` répond en moins de 200 ms en local avec ~60 k papiers et 10 prompts.
6. Le worker tient dans 4 Go de RAM avec Postgres et l'API (mesuré pendant le test du modèle).
7. CI verte (avec pgvector), lint et tests passent.

## Open Questions
- Bibliothèque d'embeddings, modèle, dimension N et seuil par défaut : tranchés par le test du modèle, qui a besoin de **10 à 20 prompts réels de l'utilisateur**.
- Python 3.14 et la bibliothèque d'embeddings : compatibles ? Sinon, l'image Docker passe en 3.13 (à décider pendant le test du modèle).
