# M3 — tâches

Commandes de vérification communes :
- Backend (depuis `backend/`) : `uv run ruff check . && uv run ruff format --check .` puis `docker compose up -d db && uv run pytest`
- Mobile (depuis `mobile/`) : `dart format --set-exit-if-changed . && flutter analyze` puis `flutter test`
- App : `docker compose up -d --build` (racine), `flutter emulators --launch Medium_Phone_API_37.0`, puis `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000` (depuis `mobile/`)

Spec : [docs/SPEC.md](../docs/SPEC.md). Chaque tâche d'écran (T27 → T34) passe avant sa PR par un aperçu de widget, une relecture avec ui-ux-pro-max (règles UX, accessibilité, guide Flutter) et emil-design-eng (finitions).

---

## Phase 1 : backend

### T20 : auteurs sans commandes LaTeX
**Description :** Une fonction pure dans `services/` convertit les commandes d'accent LaTeX des noms d'auteurs en caractères Unicode (`{\O}` → `Ø`, `{\aa}` → `å`, `\"o` → `ö`, etc., liste dans la spec). Le parseur arXiv l'applique. Une migration de données applique la même fonction aux auteurs déjà en base.

**Critères d'acceptation :**
- [x] `{\O}ystein Gullbrekken` → `Øystein Gullbrekken`, `Sondre Kvalv{\aa}g Schnell` → `Sondre Kvalvåg Schnell` ; un nom sans commande LaTeX reste identique
- [x] Les nouveaux papiers arXiv sont propres dès l'import
- [x] Après `alembic upgrade head`, plus aucun auteur en base ne contient `\` ni `{`

**Vérification :**
- [x] Lint + tests passent
- [x] Manuel : `docker compose exec db psql -U butine -d butine -c "select count(*) from papers where array_to_string(authors, ' ') ~ '[\\\\{]'"` → 0

**Dépendances :** aucune
**Fichiers :** `backend/app/services/latex.py`, `backend/app/services/feeds.py`, `backend/migrations/versions/…`, `backend/tests/test_latex.py`
**Taille :** S

### T21 : `name` et `icon` sur les prompts
**Description :** Colonnes `prompts.name` (1 à 24 caractères) et `prompts.icon` (`^[a-z0-9_]{1,40}$`), `NOT NULL`. Migration : les prompts existants reçoivent les premiers mots de leur texte comme nom et `label` comme icône. `POST /v1/prompts` les exige, `GET /v1/prompts` les renvoie. Décisions « `/v1` modifié sur place tant que rien n'est publié » et « tiroir = nom + icône » reportées dans DECISIONS.md.

**Critères d'acceptation :**
- [x] `POST /v1/prompts` sans `name` ou `icon`, avec un nom de 25 caractères ou une icône `Bad-Icon` → `422`
- [x] `GET /v1/prompts` renvoie `name` et `icon` ; l'embedding reste calculé sur `text` seul
- [x] `alembic upgrade head` passe sur la base locale existante, les prompts existants gardent leur texte

**Vérification :**
- [x] Lint + tests passent, `test_models_match_migrations` compris
- [x] Manuel : créer un prompt avec `curl` (nom, icône, texte) puis le lister

**Dépendances :** aucune
**Fichiers :** `backend/app/models.py`, `backend/migrations/versions/…`, `backend/app/api/v1/prompts.py`, `backend/tests/test_api_prompts.py`, `docs/DECISIONS.md`
**Taille :** M

### T22 : `fetched_at` dans les papiers
**Description :** `PaperOut` gagne `fetched_at`, donc `/v1/papers` et les deux feeds aussi. C'est la base du signal « New » (T31).

**Critères d'acceptation :**
- [x] `fetched_at` présent dans `/v1/papers`, `/v1/prompts/{id}/feed` et `/v1/feed`
- [x] Les autres champs et le tri ne changent pas

**Vérification :**
- [x] Lint + tests passent
- [x] Manuel : `curl localhost:8000/v1/papers?limit=1`

**Dépendances :** aucune
**Fichiers :** `backend/app/api/v1/papers.py`, `backend/tests/test_api_papers.py`, `backend/tests/test_api_feeds.py`
**Taille :** XS

### T35 : auteurs arXiv sans affiliations
**Description :** Le parseur arXiv coupe les auteurs à chaque virgule, y compris dans les parenthèses : `Joshua Terranova (Thomas Lord Department of Computer Science, University of Southern California)` donne deux « auteurs ». 311 papiers touchés sur la base locale le 2026-11-08. Le parseur ne coupe plus qu'aux virgules hors parenthèses et retire la parenthèse finale d'un nom (affiliation ou lieu). Une parenthèse au milieu du nom reste (`Haoxuan (Charlie) Zhou`). Une migration de données recolle et nettoie les auteurs déjà en base, comme T20.

**Critères d'acceptation :**
- [x] `A (Dept, Univ), B` → `["A", "B"]` ; `Haoxuan (Charlie) Zhou` reste identique ; un nom sans parenthèse reste identique
- [x] Les nouveaux papiers arXiv sont propres dès l'import ; bioRxiv inchangé
- [x] Après `alembic upgrade head`, plus aucun auteur arXiv en base ne finit par `)` ni ne contient une parenthèse non fermée

**Vérification :**
- [x] Lint + tests passent
- [x] Manuel : `docker compose exec db psql -U butine -d butine -c "select count(*) from papers where external_id like 'arxiv:%' and exists (select 1 from unnest(authors) a where a ~ '\\)$' or a ~ '\\([^)]*$')"` → 0

**Dépendances :** aucune
**Fichiers :** `backend/app/services/feeds.py`, `backend/migrations/versions/…`, `backend/tests/test_feeds.py`
**Taille :** S

### Checkpoint 1
- [x] Lint + tests backend passent, CI verte
- [x] `/v1/papers` ne renvoie plus d'auteur avec une commande LaTeX ni avec une affiliation sur la base locale
- [x] Revue humaine

---

## Phase 2 : socle mobile

### T23 : projet Flutter Android + CI
**Description :** `flutter create` dans `mobile/` (Android seulement, identifiant d'application `ch.butine` : `flutter create --org ch --project-name butine` ; décision reportée dans DECISIONS.md), `flutter_lints`, un écran « Butine » provisoire et un test de widget minimal. HTTP en clair autorisé dans le manifeste de debug seulement. Job `mobile` dans la CI : format, analyse, tests.

**Critères d'acceptation :**
- [x] `flutter run` affiche l'écran provisoire sur l'émulateur
- [x] Le job CI `mobile` passe ; le job `backend` est inchangé
- [x] Aucun dossier iOS, web ou desktop

**Vérification :**
- [x] `dart format --set-exit-if-changed . && flutter analyze && flutter test`
- [x] Manuel : l'app se lance sur l'émulateur

**Dépendances :** aucune
**Fichiers :** `docs/DECISIONS.md`, `mobile/` (généré par `flutter create`), `mobile/android/app/src/debug/AndroidManifest.xml`, `.github/workflows/ci.yml`
**Taille :** S

### T24 : thème, tokens et polices
**Description :** `theme.dart` : tokens de `palette.json` (clair et sombre), `ThemeData` Material 3 pour les deux thèmes, Inter pour l'interface et Literata pour les papiers, intégrées en `.ttf`. Un test calcule les contrastes WCAG des paires de BRAND.md. Aperçu de widget qui montre les deux thèmes.

**Critères d'acceptation :**
- [x] Les paires texte/fond de BRAND.md passent AA dans les deux thèmes (test)
- [x] Inter et Literata s'affichent sans réseau
- [x] Aucune couleur en dur hors de `theme.dart`

**Vérification :**
- [x] Analyse + tests passent
- [ ] Manuel : aperçu du thème clair et sombre sur l'émulateur

**Dépendances :** T23
**Fichiers :** `mobile/lib/ui/core/theme.dart`, `mobile/assets/fonts/…`, `mobile/pubspec.yaml`, `mobile/test/ui/core/theme_test.dart`, `mobile/lib/main.dart`
**Taille :** M

### T25 : client API généré
**Description :** Export du schéma dans `mobile/openapi.json`, configuration de swagger_parser, génération du client dans `lib/data/api/`. La liste exacte des dépendances est confirmée avec l'humain avant l'ajout. La CI régénère le schéma et le client et échoue s'il y a une différence. Décision « swagger_parser + schéma commité vérifié en CI » reportée dans DECISIONS.md.

**Critères d'acceptation :**
- [x] Le client compile et couvre les routes utilisées : users, prompts (avec `name`/`icon`), feeds (avec `fetched_at`)
- [x] Un test appelle le client contre un faux serveur HTTP local et décode un feed
- [x] Modifier un champ côté backend sans régénérer fait échouer la CI

**Vérification :**
- [x] Analyse + tests passent
- [x] `git status` propre après une régénération

**Dépendances :** T21, T22, T23
**Fichiers :** `backend/app/api/v1/{users,papers}.py` (paramètres non nullables), `mobile/openapi.json`, `mobile/swagger_parser.yaml`, `mobile/pubspec.yaml`, `mobile/lib/data/api/…` (généré), `.github/workflows/ci.yml`, `docs/DECISIONS.md`
**Taille :** M

### T26 : icônes des tiroirs et de l'app
**Description :** `drawer_icons.dart` : environ 24 icônes Material `outlined`, chacune avec un identifiant stable, et une icône par défaut pour un identifiant inconnu. La liste est montrée dans un aperçu et validée par l'humain. Icône de l'app depuis `design/logo/exports/app/` avec `flutter_launcher_icons` (avant-plan, arrière-plan, monochrome).

**Critères d'acceptation :**
- [x] Chaque identifiant respecte `^[a-z0-9_]{1,40}$` (test) ; un identifiant inconnu donne l'icône par défaut
- [x] Liste des icônes validée par l'humain
- [x] L'icône Butine apparaît sur l'écran d'accueil de l'émulateur, y compris en icône thémée

**Vérification :**
- [x] Analyse + tests passent
- [x] Manuel : icône de l'app sur l'émulateur

**Dépendances :** T24
**Fichiers :** `mobile/lib/ui/core/drawer_icons.dart`, `mobile/test/ui/core/drawer_icons_test.dart`, `mobile/pubspec.yaml`, `mobile/android/app/src/main/res/…` (généré)
**Taille :** S

### Checkpoint 2
- [x] L'app se lance sur l'émulateur, aux couleurs et polices de Butine, avec son icône
- [x] CI verte (backend + mobile, client régénéré identique)
- [x] Revue humaine (dont la liste des icônes des tiroirs)

---

## Phase 3 : parcours principal

### T27 : identité de l'appareil + premier lancement
**Description :** `device_store.dart` garde l'UUID (stockage sécurisé). Au premier lancement, `UserRepository` appelle `POST /v1/users`, puis l'écran d'accueil présente Butine et mène à la création du premier tiroir (provisoirement un écran vide jusqu'à T28). Interface en anglais : décision reportée dans DECISIONS.md.

**Critères d'acceptation :**
- [x] Premier lancement : un utilisateur est créé et son id gardé ; au lancement suivant, pas d'appel ni d'écran d'accueil
- [x] Échec réseau : message et « Retry », qui fonctionne une fois le backend relancé
- [x] Toutes les requêtes utilisateur envoient `X-User-Id`

**Vérification :**
- [x] Analyse + tests (view model et widget, faux repository)
- [ ] Manuel : désinstaller, relancer, vérifier l'utilisateur en base

**Dépendances :** T24, T25
**Fichiers :** `mobile/lib/data/device_store.dart`, `mobile/lib/data/repositories/user_repository.dart`, `mobile/lib/ui/onboarding/…`, `mobile/lib/main.dart`, `mobile/test/ui/onboarding/…`
**Taille :** M

### T28 : création d'un tiroir
**Description :** Écran « nouveau tiroir » : nom (1 à 24), choix d'une icône du jeu, texte du prompt (1 à 500), exemples de prompts courts. `403` → « The free plan includes 1 drawer. ». Ouvert depuis le premier lancement (et depuis la pastille + en T30).

**Critères d'acceptation :**
- [x] Champs validés avant l'envoi ; bouton inactif tant qu'ils sont invalides
- [x] Tiroir créé → retour au feed ; `403` → message de limite, sans bouton d'achat
- [x] Cibles tactiles ≥ 48 dp, y compris dans le choix d'icône

**Vérification :**
- [x] Analyse + tests (validation, `403`)
- [ ] Manuel : créer un tiroir en `free`, puis un 2ᵉ refusé

**Dépendances :** T26, T27
**Fichiers :** `mobile/lib/data/repositories/drawer_repository.dart`, `mobile/lib/ui/drawer/new_drawer_screen.dart`, `mobile/lib/ui/drawer/new_drawer_view_model.dart`, `mobile/test/ui/drawer/…`
**Taille :** M

### T29 : feed All
**Description :** Écran principal : feed global (`/v1/feed`), cartes (titre en Literata, auteurs, source, date), page suivante en arrivant en bas, tirer pour rafraîchir. États : chargement, vide (« Butine is reading the latest papers… » si un tiroir est `pending`, sinon « No papers yet »), erreur avec « Retry », fin de liste.

**Critères d'acceptation :**
- [x] Pagination par 50 sans doublon ni trou ; rafraîchir repart du début
- [x] Chaque état s'affiche correctement (tests de widget)
- [ ] Un tiroir créé passe de l'état « reading » à des papiers après un rafraîchissement (≤ 2 min)

**Vérification :**
- [x] Analyse + tests
- [ ] Manuel : critère de réussite 1 de la spec

**Dépendances :** T28
**Fichiers :** `mobile/lib/data/repositories/feed_repository.dart`, `mobile/lib/ui/feed/feed_screen.dart`, `mobile/lib/ui/feed/feed_view_model.dart`, `mobile/lib/ui/feed/paper_card.dart`, `mobile/test/ui/feed/…`
**Taille :** M

### T30 : pastilles + feed d'un tiroir
**Description :** Rangée de pastilles : All, un tiroir par pastille (icône + nom, ordre de création), + (création). Toucher une pastille charge le feed du tiroir et affiche le texte du prompt. Dans All, chaque carte montre l'icône et le nom de ses tiroirs. Rangée masquée avec un seul tiroir. Décision « pastilles au lieu d'une liste de tiroirs » reportée dans DECISIONS.md.

**Critères d'acceptation :**
- [x] Filtre par tiroir, texte du prompt sous la rangée, retour à All
- [x] Rangée masquée avec un seul tiroir, visible à partir de deux
- [x] Un papier retenu par deux tiroirs montre les deux dans All

**Vérification :**
- [x] Analyse + tests
- [ ] Manuel : critère de réussite 2 de la spec (3 tiroirs en `paid`)

**Dépendances :** T29
**Fichiers :** `mobile/lib/ui/feed/drawer_pills.dart`, `mobile/lib/ui/feed/feed_screen.dart`, `mobile/lib/ui/feed/feed_view_model.dart`, `mobile/lib/ui/feed/paper_card.dart`, `mobile/test/ui/feed/…`
**Taille :** M

### T31 : signal « New »
**Description :** La date de dernière ouverture du feed est gardée sur l'appareil. Les papiers dont `fetched_at` est postérieur portent le signal « New » (miel), jusqu'à l'ouverture suivante. Décision reportée dans DECISIONS.md.

**Critères d'acceptation :**
- [x] Premier affichage : aucun « New » ; ensuite, seuls les papiers arrivés depuis la dernière ouverture
- [x] La date est mise à jour à l'ouverture du feed, pas à chaque rafraîchissement
- [x] Le signal respecte BRAND.md (miel profond sur clair, miel sur sombre, jamais en texte)

**Vérification :**
- [x] Analyse + tests (horloge simulée)
- [ ] Manuel : critère de réussite 6 de la spec

**Dépendances :** T22, T29
**Fichiers :** `mobile/lib/data/device_store.dart`, `mobile/lib/ui/feed/feed_view_model.dart`, `mobile/lib/ui/feed/paper_card.dart`, `mobile/test/ui/feed/…`
**Taille :** S

### Checkpoint 3
- [ ] Critères de réussite 1, 2, 3 et 6 de la spec, à la main sur l'émulateur
- [ ] Temps de réponse du feed global noté (avec la base locale)
- [ ] Revue humaine

---

## Phase 4 : compléments

### T32 : détail d'un papier
**Description :** Toucher une carte ouvre le détail : titre, tous les auteurs, source, date, abstract complet, tiroirs concernés, bouton « Read on arXiv » / « Read on bioRxiv » qui ouvre `link` dans le navigateur.

**Critères d'acceptation :**
- [ ] Données reprises de la carte, sans nouvel appel réseau
- [ ] Le libellé du bouton suit la source ; le lien s'ouvre dans le navigateur
- [ ] Abstract en Literata, lisible dans les deux thèmes

**Vérification :**
- [ ] Analyse + tests
- [ ] Manuel : critère de réussite 4 de la spec

**Dépendances :** T29
**Fichiers :** `mobile/lib/ui/paper/paper_screen.dart`, `mobile/lib/ui/feed/paper_card.dart`, `mobile/pubspec.yaml`, `mobile/test/ui/paper/…`
**Taille :** S

### T33 : détail d'un tiroir + suppression
**Description :** Appui long sur une pastille : nom, icône, texte, état (`pending`/`ready`) et « Delete » avec confirmation dans l'écran. Après suppression, retour à All sans ce tiroir.

**Critères d'acceptation :**
- [ ] La confirmation est dans l'écran, pas une boîte de dialogue système
- [ ] Le tiroir disparaît des pastilles et du feed ; erreur réseau → message et « Retry »

**Vérification :**
- [ ] Analyse + tests
- [ ] Manuel : critère de réussite 5 de la spec

**Dépendances :** T30
**Fichiers :** `mobile/lib/ui/drawer/drawer_screen.dart`, `mobile/lib/ui/drawer/drawer_view_model.dart`, `mobile/lib/ui/feed/drawer_pills.dart`, `mobile/test/ui/drawer/…`
**Taille :** S

### T34 : réglages + choix du thème
**Description :** Écran Settings ouvert depuis le feed : thème (système, clair, sombre) gardé sur l'appareil, version de l'app, sources suivies (arXiv, bioRxiv).

**Critères d'acceptation :**
- [ ] Le thème choisi s'applique tout de suite et survit à un redémarrage
- [ ] Par défaut, le thème suit le système

**Vérification :**
- [ ] Analyse + tests
- [ ] Manuel : changer le thème, redémarrer l'app

**Dépendances :** T24
**Fichiers :** `mobile/lib/ui/settings/…`, `mobile/lib/data/device_store.dart`, `mobile/lib/main.dart`, `mobile/test/ui/settings/…`
**Taille :** S

### Checkpoint final
- [ ] Tous les critères de réussite de docs/SPEC.md remplis (dont le 8 : backend arrêté → erreurs avec « Retry », sans plantage)
- [ ] Décisions de la spec reportées dans DECISIONS.md
- [ ] CI verte
- [ ] Revue humaine avant la suite (compte anonyme, paiement)

---

## Notes pour plus tard

- **Feed qui attend un tiroir `pending`** : « Butine is reading the latest papers… » ne se met pas à jour tout seul ; il faut tirer pour rafraîchir. À faire : rafraîchir automatiquement le feed tant qu'un tiroir est `pending`. Remarqué au test de T29.
- **Retour de `paid` à `free`** : un utilisateur qui se désabonne avec plusieurs tiroirs ne doit plus pouvoir les modifier. Règle exacte à décider (tiroirs gelés, ou seul le plus ancien reste actif). À traiter avec le paiement, hors M3.
- **Deux tiroirs en `free`** : le plan gratuit devrait inclure 2 tiroirs, pas 1. À changer : limite `free` côté backend (`PROMPT_LIMITS`), message « The free plan includes 1 drawer. » dans l'app, DECISIONS.md et SPEC.md. Demandé au test de T30.
- **+ en pastille** : au bout de la rangée, le + est une pastille comme les autres (demandé au test de T30, fait avec T31). Sans la rangée, il reste un bouton dans la barre.
- **« New » et le retour à l'app** : l'ouverture ne compte qu'au lancement de l'écran du feed (démarrage, ou retour après la création d'un tiroir). Revenir à l'app laissée en arrière-plan ne déplace pas la ligne. À revoir si c'est gênant à l'usage.
