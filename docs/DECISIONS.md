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
- **Tout est en anglais** (papiers et prompts) : modèle d'embeddings anglais local (gratuit, sans API externe). Choix du modèle en M2 après un test sur 10–20 vrais prompts ; probablement un petit modèle généraliste de recherche (bge, e5) plutôt qu'un modèle papier ↔ papier (SPECTER2).
- Un papier entre dans le tiroir d'un prompt si sa similarité dépasse un **seuil global**, réglé côté serveur (variable d'environnement). Pas de réglage par l'utilisateur ni de 👍/👎 pour l'instant.
- **Un feed (« tiroir ») par prompt**, plus un **feed global** qui regroupe tous les tiroirs de l'utilisateur.
- À la création d'un prompt : rattrapage sur les papiers des 7 derniers jours (configurable).
- Pas de digest hebdomadaire pour l'instant.
- Plus tard : LLM pour les résumés, uniquement sur les papiers qui correspondent à un prompt (jamais tout le catalogue : ~50 k papiers par mois).

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
- Compatibilité de torch / sentence-transformers avec Python 3.14 (sinon 3.13 dans l'image Docker) — M2.
- URL du flux RSS bioRxiv (les anciennes URLs `connect.biorxiv.org/biorxiv_xml/…` renvoient 404) — tâche catalogue.
- Conditions d'utilisation des flux arXiv et bioRxiv pour un usage commercial — avant la publication.
- Cadre juridique des résumés IA (directive DSM art. 15, opt-out TDM) — avant les résumés.
- Prix Infomaniak, Apple, Google, RevenueCat, Codemagic — avant de les budgéter.
