# Décisions — Butine

Résultat de la session de cadrage du 2026-10-15, révisée le 2026-10-27 (recentrage sur les papiers scientifiques). Idée : [IDEE.md](IDEE.md).
Chaque décision a sa raison ; si la raison ne tient plus, la décision peut changer.

## Objectif
Vrai produit de veille scientifique, publié sur les stores (iOS + Android) et monétisé. Il doit être **rentable, sans plus** : les revenus couvrent les coûts (hébergement, comptes développeur, commission des stores).
Le projet reste aussi un terrain d'apprentissage d'outils de gros projets.
→ Tout ce que les stores exigent doit exister (comptes supprimables, backend public HTTPS, respect du contenu).

_À l'origine (2026-10-15) : projet d'apprentissage généraliste (presse, YouTube…), sans publication ni monétisation._

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
- **Tout arXiv + bioRxiv**. Une source par archive arXiv (`cs`, `math`, `physics`…, ~20) : un flux en panne n'affecte que son archive, backoff et stats par archive. bioRxiv est choisi parce qu'il pose d'autres problèmes qu'arXiv : format RSS 1.0 (RDF), DOI au lieu d'identifiants arXiv, versions, données parfois mal formées.
- bioRxiv : une source par sujet (~27, `connect.biorxiv.org/biorxiv_xml.php?subject=<sujet>`), car chaque flux ne contient que les 30 derniers papiers. Un sujet qui publie plus de 30 papiers entre deux passages en perd ; à surveiller, l'API JSON `api.biorxiv.org` est le recours.
- Volume mesuré le 2026-10-27 : ~3 000 nouveaux papiers arXiv sur une journée, + ~150–200 bioRxiv ; soit ~50–60 k papiers par mois. Coût négligeable face aux frais fixes (≈ 300 Mo en base, quelques minutes d'embeddings par jour). Le vrai coût est le bruit : la qualité du matching compte d'autant plus.
- **Catalogue fixe** dans `backend/sources.yaml`, synchronisé en base par une commande `sync-sources` : ajoute les nouvelles, **désactive** (ne supprime pas) les retirées. Pas d'endpoint d'ajout de source.
- **Sources imposées** : l'utilisateur ne choisit pas ses sources (pas d'abonnement, rien à cocher) et ne peut pas en ajouter. Chaque prompt est comparé à tous les papiers du catalogue.
- Sources globales, récupérées une seule fois pour tout le monde.
- On ne stocke que ce que fournit le flux (titre, auteurs, abstract, lien…). Pas d'aspiration des PDF. Les futurs résumés IA partent de l'abstract.

## Modèle `Paper`
- `external_id` **unique dans tout le catalogue** : `arxiv:2410.12345` ou `doi:10.1101/…`. Un papier présent dans plusieurs catégories n'apparaît qu'une fois.
- Version : une nouvelle version (`v2`) **met à jour** le papier existant, elle ne crée pas de nouvelle entrée.
- Champs : titre, auteurs (liste), abstract **complet** (pas tronqué : c'est ce que lit l'IA), catégories (liste), lien, date de publication, version.
- Une seule source par papier : la première qui l'a apporté. Pas de table de liaison papier ↔ source.
- Pas de table d'auteurs tant que « suivre un auteur » n'existe pas.
- Limite connue : un même papier publié sur arXiv **et** bioRxiv a deux identifiants différents et n'est pas détecté comme doublon. Comparaison par titre normalisé : plus tard, si le cas se présente vraiment.

## Récupération (worker)
- Simple boucle Python dans son conteneur. Pas de Celery/Redis tant que la règle ci-dessous ne le demande pas.
- Chaque flux toutes les 30 min ; requêtes conditionnelles (`ETag` / `If-Modified-Since`). arXiv ne publie qu'une fois par jour : les 304 rendent ces appels gratuits.
- Dédoublonnage par `external_id`.
- Erreurs : backoff progressif, source désactivée après ~10 échecs consécutifs (erreur conservée).
- Purge des papiers après 30 jours (configurable), à revoir plus tard.

## Observabilité et seuil Celery
- Une ligne de log structurée par cycle : durée, flux interrogés, nouveaux papiers, erreurs, papiers en attente d'embedding.
- Mêmes chiffres via `GET /v1/stats`.
- **Règle** : si un cycle dépasse ~50 % de l'intervalle, ou si la file d'embeddings grossit d'un cycle à l'autre → passer à une file de tâches (Celery + Redis).
- Prometheus/Grafana : plus tard, avec l'exercice Kubernetes.

## IA et feeds
- Prompt = texte libre en anglais. Pas d'exclusions ni de mots-clés pour l'instant.
- **Tout est en anglais** (papiers et prompts) : modèle d'embeddings anglais local (gratuit, sans API externe).
- **Modèle : `ibm-granite/granite-embedding-small-english-r2`** via `fastembed` (ONNX, sans torch, tourne sur Python 3.14). Licence Apache 2.0, **N = 384**, pas de préfixe requête/document. fastembed ne normalise pas ce modèle : le worker normalise lui-même. Lots de 2 textes (contexte de 8 192 tokens : de gros lots d'abstracts longs font exploser la RAM).
- **`MATCH_THRESHOLD` = 0,84** par défaut (précision 0,62, rappel 0,88 sur le test ; 0,82 → 0,50 / 0,96 ; 0,86 → 0,79 / 0,59).
- Test (novembre 2026) : 10 modèles sur 19 prompts et ~8 700 papiers, pertinence jugée à la main sur le top 10. `scripts/match_preview.py` ne garde que granite-s, pour réajuster le seuil.

  | Modèle | P@5 | Rappel top 10 | MRR | F1 seuil global | min / 3 000 papiers | RAM |
  |---|---|---|---|---|---|---|
  | **granite-s** | **0,53** | **0,68** | 0,86 | 0,75 | **6,5** | 1,2 Go |
  | arctic-embed-l-v2.0 | 0,51 | 0,62 | 0,94 | 0,74 | 62,8 | 2,7 Go |
  | bge-base-en-v1.5 | 0,51 | 0,61 | 0,89 | 0,65 | 21,9 | 1,8 Go |
  | bge-large-en-v1.5 | 0,51 | 0,62 | 0,87 | 0,76 | 72,4 | 3,7 Go |
  | nomic-embed-text-v1.5 | 0,51 | 0,54 | 0,76 | 0,68 | 24,1 | 1,8 Go |
  | embeddinggemma-300m | 0,50 | 0,67 | 0,82 | 0,71 | 18,4 | 1,9 Go |
  | Qwen3-Embedding-0.6B | 0,50 | 0,62 | 0,89 | 0,78 | 103,1 | 2,5 Go |
  | bge-small-en-v1.5 | 0,47 | 0,62 | 0,86 | 0,67 | 7,7 | 0,95 Go |
  | arctic-embed-s | 0,47 | 0,56 | 0,77 | 0,67 | 7,1 | 1,4 Go |
  | e5-small-v2 | 0,37 | 0,49 | 0,73 | 0,54 | 7,1 | 1,4 Go |

  - Les écarts entre les meilleurs modèles sont dans le bruit d'un test de 19 prompts : on prend le moins cher.
  - Avec un seuil global, le F1 plafonne vers 0,75 quel que soit le modèle : l'échelle des scores varie d'un prompt à l'autre, et un prompt sans papier pertinent laisse passer 1 ou 2 papiers hors sujet.
  - Les prompts courts (« sodium-ion battery cathode materials ») marchent mieux que les longues phrases, pour tous les modèles.
  - Rerankers (bge-reranker-base, bge-reranker-v2-m3 sur le top 50) : **écartés**, moins bons que granite-s seul (P@5 0,40 et 0,44), 22 à 77 s par prompt, 3 à 4 Go de RAM.
  - SPECTER2 : non mesuré (OOM au-delà de 6 Go avec torch).
- Un papier entre dans le tiroir d'un prompt si sa similarité dépasse un **seuil global**, réglé côté serveur (variable d'environnement). Pas de réglage par l'utilisateur ni de 👍/👎 pour l'instant.
- **Un feed (« tiroir ») par prompt**, plus un **feed global** qui regroupe tous les tiroirs de l'utilisateur.
- Un tiroir a un **nom court** (1 à 24 caractères) et une **icône monochrome** choisie dans un jeu fermé de l'app (identifiant `^[a-z0-9_]{1,40}$` stocké dans `prompts.icon`). L'embedding reste calculé sur le texte seul. Pas de renommage en M3.
- À la création d'un prompt : rattrapage sur les papiers des 7 derniers jours (configurable).
- Pas de digest hebdomadaire pour l'instant.
- Plus tard : LLM pour les résumés, uniquement sur les papiers qui correspondent à un prompt (jamais tout le catalogue : ~50 k papiers par mois).
- Pistes d'amélioration (pas pour le MVP) :
  - **Réglage de sensibilité par feed** (« plus de résultats » ↔ « plus précis ») : décale le seuil pour ce prompt. Raison : l'échelle des scores varie d'un prompt à l'autre, un seuil global plafonne vite.
  - **Suggestions « à côté »** : quelques papiers juste sous le seuil, affichés à part (« Ça pourrait aussi vous intéresser »), pour la découverte.
  - **Juge LLM sur les candidats** : les embeddings présélectionnent ~10 papiers par prompt et par jour, un LLM tranche (pertinent / proche / hors sujet). Règle le seuil global et les suggestions « à côté ». Coût estimé pour ~300 prompts : ~6 $/mois avec Claude Haiku 5.5, ~10–40 CHF/mois chez Infomaniak AI Services (données en Suisse). Jamais sur tout le catalogue (~1 000 $/mois même avec Haiku). À tester sur les prompts du test avant de décider.

## Offre et paiement
- Gratuit : 1 prompt. Payant : 10 prompts pour **5 CHF/mois** (≈ 4,25 CHF net après 15 % de commission → ~6 abonnés couvrent ~25 CHF/mois de frais fixes). Prix annuel à fixer à la publication.
- Le feed global ne compte pas dans la limite : c'est une vue sur les tiroirs.
- Changer de prix : une baisse s'applique sans souci ; une hausse est notifiée aux abonnés et peut en faire partir (possibilité de garder l'ancien prix pour eux). Viser juste dès le départ.
- Paiement par achats intégrés des stores (obligatoire pour un abonnement numérique), via RevenueCat. Rien à coder avant l'app Flutter (M3).
- Le backend stocke le plan de l'utilisateur (`free` / `paid`), mis à jour par webhook RevenueCat, et applique la limite de prompts.
- Retour au gratuit : tous les prompts sont conservés ; un seul reste actif (choisi par l'utilisateur, sinon le plus ancien), les autres sont gelés et se réactivent au réabonnement.

## Comptes
1. Table `users` dès M2, sans authentification (id passé à l'API), avec le plan (`free` par défaut).
2. Compte anonyme automatique (jeton stocké sur l'appareil). Il suffit pour payer : « Restaurer mes achats » des stores retrouve l'abonnement sur un nouvel appareil.
3. Lien d'un email par lien magique (optionnel, multi-appareils). Pas de mot de passe.
- Suppression du compte depuis l'app (exigence des stores).

## API
- REST/JSON, toutes les routes sous `/v1`. Raison : les anciennes apps mobiles restent installées et doivent continuer à fonctionner.
- Nouvelle version seulement en cas de changement cassant (renommer/supprimer un champ, nouveau paramètre obligatoire). Alors `api/v2/` à côté de `api/v1/`, les deux appellent les mêmes `services/` ; jamais de `if v1` dans la logique.
- `/v1` modifié sur place tant qu'aucune app n'est publiée (aucun ancien client à protéger) ; `/v2` seulement après la première publication.
- Client Dart généré depuis le schéma OpenAPI (M3).

## Tests
- `pytest` sur un vrai Postgres en Docker, flux RSS de test en fichiers XML locaux, aucun appel réseau.
- Priorités : parsing, dédoublonnage, backoff, synchronisation du catalogue.

## Hébergement
- En local jusqu'au jalon « prêt stores ».
- Puis un VPS Infomaniak avec ≥ 4 Go de RAM (Postgres + API + modèle d'embeddings ; 1 Go est trop juste). Vérifier les prix au moment venu.

## Jalons
- **M1** : catalogue arXiv + bioRxiv + worker de récupération + API (sources, papiers) + Compose + CI.
- **M2** : utilisateurs (avec plan), prompts et limite par plan, matching par embeddings, feed par prompt + feed global.
- **M3** : app Flutter minimale qui affiche les feeds (+ client généré depuis OpenAPI).
- **Ensuite** : compte anonyme, paiement (RevenueCat + webhook), email, suppression de compte, résumés IA, déploiement Infomaniak (images Docker avec utilisateur non-root), compilation iOS en CI, Kubernetes.

## À vérifier plus tard
- Conditions d'utilisation des flux arXiv et bioRxiv pour un usage commercial — avant la publication.
- Cadre juridique des résumés IA (directive DSM art. 15, opt-out TDM) — avant les résumés.
- Prix Infomaniak, Apple, Google, RevenueCat, Codemagic — avant de les budgéter.
- Recherche d'antériorité de la marque « Butine » et du symbole (IPI suisse, EUIPO, recherche d'image inversée) — avant la publication sur les stores. Le symbole est un hexagone, forme fréquente dans la tech.
- Vitesse de `/v1/feed` : 141 à 177 ms avec 60 k papiers et 10 prompts (fin de M2), pour un objectif de 200 ms. Le coût croît avec papiers × prompts. Avant d'ajouter des sources ou de relever la limite `paid` : faire remplir par le worker une table `matches(prompt_id, paper_id, score)` au moment d'embedder, pour que le feed ne fasse plus qu'une lecture par index.
- Limite de débit sur l'API — avant le déploiement public. `POST /v1/users` crée des comptes sans limite, et chaque appel au feed coûte environ 150 ms de calcul à Postgres.
