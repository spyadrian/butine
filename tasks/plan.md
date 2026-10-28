# Plan d'implémentation : jalon M2 — utilisateurs, prompts, matching, feeds

## Vue d'ensemble
M2 permet à un utilisateur de créer des prompts en anglais (1 en `free`, 10 en `paid`) et de lire, pour chacun, un tiroir de papiers proches. Un feed global regroupe ses tiroirs. Le worker calcule les embeddings avec un modèle local, stockés dans pgvector. Le matching se fait à la volée en SQL.
Référence : [docs/SPEC.md](../docs/SPEC.md) (contrats, règles, critères de réussite), [docs/DECISIONS.md](../docs/DECISIONS.md). Ce plan n'y ajoute que l'ordre des tâches et quelques choix d'implémentation.

## Choix d'implémentation (nouveaux, à valider)
| Choix | Raison |
|---|---|
| Numérotation qui continue celle de M1 (T12 → T19) | « T3 » ne peut pas désigner deux tâches différentes en discussion. |
| Le test du modèle (T12) passe en premier | C'est le risque principal : il fixe la bibliothèque, la dimension des vecteurs (donc la migration de T15), la version de Python et la RAM. S'il échoue, le reste de M2 change. |
| T12 et T13 sont indépendantes | T12 attend les prompts de l'utilisateur. En attendant, T13 et T14 peuvent avancer. |
| Script `backend/scripts/match_preview.py` gardé dans le dépôt | Il affiche les meilleurs papiers d'un prompt avec leur score ; il resservira pour réajuster le seuil avec de vrais retours. |
| pgvector et colonnes (T15) séparés du calcul des embeddings (T16) | T15 change l'image Postgres (Compose + CI) : une PR d'infrastructure à part, facile à vérifier et à annuler. |
| Modèle téléchargé au build de l'image du worker | Pas de téléchargement à chaque redémarrage, ni de dépendance réseau au démarrage. Détail réglé en T16. |

## Graphe de dépendances
```
T12 test du modèle (bibliothèque, modèle, N, seuil, Python)
 └──────────────┐
T13 users + set-plan          │
 └── T14 prompts + limite     │
      └── T15 pgvector + colonnes vector(N) ◄┘
           └── T16 embeddings calculés par le worker
                ├── T17 compteurs d'embeddings dans les stats
                └── T18 feed d'un prompt
                     └── T19 feed global
```
T15 a besoin de N (T12) et de la table `prompts` (T14). T17 et T18 sont indépendantes une fois T16 faite.

## Liste des tâches
Détail (critères, vérifications, fichiers) dans [todo.md](todo.md).

### Phase 1 : risque et comptes
- [ ] T12 : test du modèle d'embeddings, décision notée dans DECISIONS.md
- [ ] T13 : table `users`, `POST /v1/users`, commande `set-plan`
- [ ] T14 : prompts (créer, lister, supprimer) avec la limite par plan

### Checkpoint 1
- [ ] Créer un utilisateur et un prompt avec `curl` ; 2ᵉ prompt refusé en `free`, accepté après `set-plan … paid`
- [ ] Modèle et seuil validés par l'humain

### Phase 2 : embeddings
- [ ] T15 : pgvector (Compose + CI) et colonnes d'embedding
- [ ] T16 : le worker calcule les embeddings des prompts et des papiers
- [ ] T17 : `embedded_papers` et `pending_embeddings` dans le log et `/v1/stats`

### Checkpoint 2
- [ ] `docker compose up` → `pending_embeddings` redescend à 0, un nouveau prompt passe à `ready` en ≤ 2 min
- [ ] RAM du worker mesurée, compatible avec 4 Go

### Phase 3 : feeds
- [ ] T18 : `GET /v1/prompts/{id}/feed`
- [ ] T19 : `GET /v1/feed` (feed global)

### Checkpoint final
- [ ] Tous les critères de réussite de docs/SPEC.md remplis (dont `/v1/feed` < 200 ms avec ~60 k papiers)
- [ ] CI verte, revue humaine avant M3

## Risques et mitigations
| Risque | Impact | Mitigation |
|---|---|---|
| Bibliothèque d'embeddings incompatible avec Python 3.14 | Moyen | Vérifié en T12 ; sinon `python:3.13-slim` et `requires-python` ajusté en T16. |
| Le seuil global sépare mal le bon du bruit | Haut | T12 le mesure sur de vrais prompts ; `MATCH_THRESHOLD` reste réglable sans redéploiement de code ; `match_preview.py` pour le réajuster. |
| torch alourdit l'image et la RAM | Moyen | `fastembed` (ONNX) testé en T12 ; seul le worker charge le modèle. |
| Rattrapage initial long (~4 000 papiers, puis ~60 k en régime plein) | Moyen | `EMBED_BATCH_LIMIT` borne chaque cycle ; `pending_embeddings` (T17) rend la file visible ; règle Celery de DECISIONS.md. |
| Matching à la volée trop lent | Moyen | Mesuré au checkpoint final avec ~60 k papiers ; recours prévu par la spec : index HNSW ou table de correspondances. |
| Changement d'image Postgres qui casse la base locale | Faible | `pgvector/pgvector:pg18` est Postgres 18 plus l'extension : même format de données, le volume est réutilisé. |
| Changement de modèle plus tard (dimension différente) | Faible | Une migration qui change N et remet tous les embeddings à `NULL` ; le worker recalcule. |

## Open Questions
- Les 10 à 20 prompts réels de l'utilisateur, nécessaires pour T12.
