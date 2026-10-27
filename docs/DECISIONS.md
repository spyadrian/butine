# Décisions — Butine

Résultat de la session de cadrage du 2026-10-15. Idée d'origine : [IDEE.md](IDEE.md).
Chaque décision a sa raison ; si la raison ne tient plus, la décision peut changer.

## Objectif
Vrai produit, publié sur les stores (iOS + Android) et monétisé (gratuit : 1 feed ; payant : 10 feeds ou plus). Il doit être **rentable, sans plus** : les revenus couvrent les coûts (hébergement, comptes développeur, frais des stores).
Le projet reste aussi un terrain d'apprentissage d'outils de gros projets.
→ Tout ce que les stores exigent doit exister (comptes supprimables, backend public HTTPS, respect du contenu).

_Révisé le 2026-10-27 : à l'origine, projet d'apprentissage sans publication ni monétisation, recentré depuis sur les papiers scientifiques (voir [IDEE.md](IDEE.md))._

## Stack
| Choix | Raison |
|---|---|
| Backend Python + FastAPI | Écosystème IA (embeddings, LLM) le plus simple ; OpenAPI généré automatiquement. |
| SQLAlchemy 2 + Alembic | ORM standard ; migrations versionnées indispensables dès qu'une base de prod contient des données. |
| PostgreSQL dès M1 (pgvector en M2) | Compose le rend gratuit ; SQLite gère mal API + worker en écriture ; évite une migration de BDD. |
| Mobile Flutter | Un seul code iOS + Android ; Python mobile n'est pas au niveau store. |
| Monorepo `backend/` `mobile/` `docs/` | Un changement d'API et son usage mobile dans le même commit. |
| Docker Compose (api, worker, db) | Utile dès M1. |
| GitHub + Actions (pytest + ruff) dès M1 | Runner macOS disponible pour compiler iOS plus tard. |
| Kubernetes : plus tard, comme exercice | Overkill pour 3 conteneurs ; à faire volontairement (k3s ou K8s managé Infomaniak). |

## Plateformes
- Développement et tests sur Android (Linux). iOS compilé uniquement via CI macOS au jalon « prêt stores ».
- Compte Apple Developer (99 $/an) seulement quand la publication approche : c'est un coût récurrent à couvrir.

## Sources et contenu
- Uniquement des papiers scientifiques, via RSS/Atom. Pas de presse, de YouTube ni de réseaux sociaux.
- Pour commencer : arXiv + bioRxiv. bioRxiv est choisi parce qu'il pose d'autres problèmes qu'arXiv : format RSS 1.0 (RDF), identifiants DOI au lieu d'identifiants arXiv, versions (`v1`, `v2`), données parfois mal formées.
- **Catalogue fixe** dans `backend/sources.yaml`, synchronisé en base par une commande `sync-sources` : ajoute les nouvelles, **désactive** (ne supprime pas) les retirées. Pas d'endpoint d'ajout de source.
- **Sources imposées** : l'utilisateur ne choisit pas ses sources (pas d'abonnement, rien à cocher) et ne peut pas en ajouter. Chaque prompt est comparé à tous les papiers du catalogue.
- Sources globales, récupérées une seule fois pour tout le monde.
- Rétention : 30 jours, à revoir plus tard.
- On ne stocke que ce que fournit le flux (titre, source, extrait, lien). Pas d'aspiration des articles (droit d'auteur, rejet store). Les futurs résumés IA partent du contenu du flux.

## Récupération (worker)
- Simple boucle Python dans son conteneur. Pas de Celery/Redis tant que la règle ci-dessous ne le demande pas.
- Chaque flux toutes les 30 min ; requêtes conditionnelles (`ETag` / `If-Modified-Since`).
- Dédoublonnage par `guid`, sinon par lien.
- Erreurs : backoff progressif, source désactivée après ~10 échecs consécutifs (erreur conservée).
- Purge des articles après 30 jours (configurable).

## Observabilité et seuil Celery
- Une ligne de log structurée par cycle : durée, flux interrogés, nouveaux articles, erreurs, articles en attente d'embedding.
- Mêmes chiffres via `GET /v1/stats`.
- **Règle** : si un cycle dépasse ~50 % de l'intervalle, ou si la file d'embeddings grossit d'un cycle à l'autre → passer à une file de tâches (Celery + Redis).
- Prometheus/Grafana : plus tard, avec l'exercice Kubernetes.

## IA
- Sujet = texte libre + précision optionnelle. Pas d'exclusions ni de mots-clés pour l'instant.
- Matching par embeddings multilingues locaux + seuil de similarité (gratuit, sans API externe). Un article correspond quelle que soit sa langue.
- À la création d'un sujet : rattrapage sur les articles des 7 derniers jours (configurable).
- Plus tard : LLM pour les résumés et éventuellement les cas limites (approche hybride). Un LLM pour chaque article × sujet coûterait trop cher.

## Comptes
1. Table `users` dès M2, sans authentification (id passé à l'API).
2. Compte anonyme automatique (jeton stocké sur l'appareil).
3. Lien d'un email par lien magique (optionnel, multi-appareils). Pas de mot de passe.
- Suppression du compte depuis l'app (exigence des stores).

## API
- REST/JSON, toutes les routes sous `/v1`. Raison : les anciennes apps mobiles restent installées et doivent continuer à fonctionner.
- Nouvelle version seulement en cas de changement cassant (renommer/supprimer un champ, nouveau paramètre obligatoire). Alors `api/v2/` à côté de `api/v1/`, les deux appellent les mêmes `services/` ; jamais de `if v1` dans la logique.
- Client Dart généré depuis le schéma OpenAPI (M3).

## Tests
- `pytest` sur un vrai Postgres en Docker, flux RSS de test en fichiers XML locaux, aucun appel réseau.
- Priorités : parsing, dédoublonnage, backoff, synchronisation du catalogue.

## Hébergement
- En local jusqu'au jalon « prêt stores ».
- Puis un VPS Infomaniak avec ≥ 4 Go de RAM (Postgres + API + modèle d'embeddings ; 1 Go est trop juste). Vérifier les prix au moment venu.

## Jalons
- **M1** : catalogue `sources.yaml` + worker de récupération + API (sources, articles) + Compose + CI.
- **M2** : utilisateurs, sujets, matching par embeddings, `GET /v1/feed`.
- **M3** : app Flutter minimale qui affiche le fil (+ client généré depuis OpenAPI).
- **Ensuite** : compte anonyme, puis email, suppression de compte, résumés IA, déploiement Infomaniak (images Docker avec utilisateur non-root), compilation iOS en CI, Kubernetes.

## À vérifier plus tard
- Compatibilité de torch / sentence-transformers avec Python 3.14 (sinon 3.13 dans l'image Docker) — M2.
- Cadre juridique des résumés IA (directive DSM art. 15, opt-out TDM) — avant les résumés.
- Prix Infomaniak, Apple, Google, Codemagic — avant de les budgéter.
