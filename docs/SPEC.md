# Spec : jalon M3 — app Flutter minimale

Référence : [DECISIONS.md](DECISIONS.md), marque : [BRAND.md](BRAND.md), logo et palette : [design/logo/](../design/logo/). Spec précédente : [SPEC-M2.md](SPEC-M2.md).
Cette spec n'ajoute que ce qui est nécessaire pour coder M3 ; en cas de conflit, la décision la plus récente l'emporte et l'autre document est mis à jour.

## Objectif
Un ingénieur R&D installe Butine sur Android, crée ses **tiroirs** (un nom court, une icône, un prompt en anglais) et lit chaque matin les papiers retenus pour lui : tous ensemble dans **All**, ou tiroir par tiroir grâce à une rangée de **pastilles** en haut du feed. Il referme l'app rassuré : c'est trié, il n'a rien raté.

M3 se termine quand ce parcours fonctionne de bout en bout sur un émulateur Android contre le backend local, avec l'identité de BRAND.md (palette, Inter, Literata, logo, thèmes clair et sombre).

**Hors périmètre M3 :** iOS, paiement et passage en `paid` depuis l'app, compte anonyme durable (jeton signé), email, suppression de compte, notifications, renommer un tiroir ou changer son icône, résumés IA, 👍/👎, site vitrine, déploiement public.

## Carte des capacités

| Module | Rôle | Dépend de |
|---|---|---|
| `backend-m3` | Auteurs sans LaTeX ; `name` et `icon` sur les prompts ; `fetched_at` dans les papiers | — |
| `api-client` | Schéma OpenAPI figé dans le repo, client Dart généré par swagger_parser | `backend-m3` |
| `design-system` | Thème Flutter (tokens, polices, clair/sombre), jeu d'icônes des tiroirs, icône de l'app | — |
| `app` | Écrans, navigation, état, identité de l'appareil | `api-client`, `design-system` |

Ordre de construction : `backend-m3` et `design-system` (indépendants) → `api-client` → `app`.

### `backend-m3`
Changements additifs ou internes, aucun client publié n'existe : `/v1` est modifié sur place (voir « Décisions à reporter »).
- **Auteurs sans LaTeX.** Le parseur arXiv convertit les commandes d'accent LaTeX en caractères Unicode : `{\O}ystein` → `Øystein`, `Kvalv{\aa}g` → `Kvalvåg`, `\"o`/`{\"o}` → `ö`, `\'e` → `é`, ainsi que `` \` ``, `\^`, `\~`, `\c{c}`, `\v{s}`, `\o`, `\aa`, `\ss`, `\l`. Fonction pure dans `services/`, sans nouvelle dépendance. Une migration de données applique la même fonction aux auteurs déjà en base.
- **Nom et icône d'un tiroir.** Colonnes `prompts.name` (1 à 24 caractères après suppression des espaces autour) et `prompts.icon` (identifiant, `^[a-z0-9_]{1,40}$`), toutes deux `NOT NULL`.
  - Migration : les prompts existants reçoivent comme `name` les premiers mots de leur `text` (24 caractères au plus) et `icon = "label"`.
  - `POST /v1/prompts {"name", "icon", "text"}` : les trois sont obligatoires, `422` sinon. `GET /v1/prompts` renvoie `name` et `icon`.
  - Le backend ne connaît pas la liste des icônes : il valide seulement la forme de l'identifiant. L'app affiche une icône par défaut pour un identifiant inconnu.
  - L'embedding reste calculé sur `text` seulement.
- **`fetched_at` dans les papiers.** `PaperOut` (donc les deux feeds) gagne `fetched_at` : c'est ce qui permet à l'app de marquer les papiers arrivés depuis la dernière visite (« New »). `published_at` ne convient pas : arXiv publie une fois par jour et un papier peut être récupéré après la date annoncée.

### `api-client`
- Le schéma OpenAPI est exporté sans lancer de serveur et **commité** dans `mobile/openapi.json` :
  `uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > ../mobile/openapi.json` (depuis `backend/`).
- swagger_parser génère le client Dart à partir de ce fichier, dans `mobile/lib/data/api/`. Le code généré est commité et n'est jamais modifié à la main.
- La CI régénère le schéma et le client et échoue s'il y a une différence : un changement d'API oublié côté app casse la CI, pas l'app en production.
- Le client envoie `X-User-Id` sur toutes les routes utilisateur. URL du backend : `--dart-define=API_BASE_URL=…`, défaut `http://10.0.2.2:8000` (l'hôte vu depuis l'émulateur Android). Le HTTP en clair est autorisé **en debug seulement**.

### `design-system`
- **Tokens** repris de `design/logo/palette.json` : fond, texte, gris de métadonnées, miel, miel profond, grenat (erreur), avec leurs valeurs claires et sombres. Les règles de BRAND.md s'appliquent : jaune rare (bouton principal, signal « New »), jamais de miel pour du texte sur fond clair, erreurs en grenat avec icône et texte, pas de dégradé ni de pastille rouge.
- **Polices intégrées** à l'app (fichiers `.ttf`, OFL) : Inter pour l'interface, Literata pour les titres et abstracts des papiers. Aucune police téléchargée à l'exécution.
- `ThemeData` clair et sombre (Material 3) construits depuis les tokens ; le thème suit le système par défaut.
- **Jeu d'icônes des tiroirs** : une liste fermée d'environ 24 icônes **monochromes** au trait, prises dans les Material Icons fournies avec Flutter (variantes `outlined`, sans dépendance). Chaque icône a un identifiant stable (`battery_charging_full`, `show_chart`, `memory`, `science`…) ; c'est cet identifiant qui est stocké dans `prompts.icon`. La liste exacte est choisie dans la tâche correspondante.
- **Icône de l'app** : depuis `design/logo/exports/app/` (icône adaptative Android : avant-plan, arrière-plan, monochrome). Le splash est celui d'Android 12+ (icône sur fond miel), sans écran de démarrage maison.

### `app`
Écrans décrits par leur fonction ; le rendu visuel est décidé pendant les tâches, en code, avec les skills de design (voir « Boundaries »).

1. **Premier lancement.** Si l'appareil n'a pas d'identifiant, l'app appelle `POST /v1/users` et garde l'UUID renvoyé dans un stockage sécurisé. Un écran présente Butine en une ou deux phrases et mène à la création du premier tiroir. En cas d'échec réseau : message et « Retry ». On ne revoit plus cet écran ensuite.
2. **Feed (écran principal).**
   - Rangée de pastilles qui défile horizontalement : **All** en premier, puis un tiroir par pastille (icône + nom, ordre de création), puis **+** pour créer un tiroir. La rangée est masquée tant qu'il n'y a qu'un tiroir ; le **+** passe alors dans la barre du haut.
   - Sous la rangée : le texte complet du prompt du tiroir sélectionné ; dans All, le nombre de tiroirs.
   - Liste des papiers : titre (Literata), auteurs, source, date ; dans All, l'icône et le nom du ou des tiroirs qui ont retenu le papier (`prompt_ids`). Le signal « New » (miel) marque les papiers dont `fetched_at` est postérieur à la dernière ouverture du feed, gardée sur l'appareil.
   - Tirer pour rafraîchir ; page suivante chargée en arrivant en bas (`limit` 50, `offset`).
   - États : chargement, vide (« Butine is reading the latest papers… » pour un tiroir `pending`, « No papers yet » sinon), erreur réseau avec « Retry », fin de liste.
3. **Détail d'un tiroir** (depuis un appui long sur sa pastille) : nom, icône, texte, état (`pending`/`ready`), et **Delete** avec confirmation dans l'écran (pas de boîte de dialogue système).
4. **Nouveau tiroir** (depuis **+** ou le premier lancement) : nom (1 à 24 caractères), choix d'une icône du jeu, texte du prompt (1 à 500 caractères), quelques exemples de prompts courts et précis. Limite du plan atteinte (`403`) : « The free plan includes 1 drawer. », sans bouton d'achat.
5. **Détail d'un papier** (toucher une carte) : titre, tous les auteurs, source, date, abstract complet, tiroirs concernés, et « Read on arXiv » / « Read on bioRxiv » qui ouvre `link` dans le navigateur. Les données viennent de la carte : pas de nouvelle route.
6. **Settings** (depuis le feed) : thème (système, clair, sombre, gardé sur l'appareil), version de l'app, sources suivies (arXiv, bioRxiv).

Interface **en anglais** (comme les papiers et les prompts), sans système de traduction en M3.

## Tech Stack
- Backend : celui de M2, sans nouvelle dépendance.
- Mobile : Flutter stable (3.47) et Dart 3.13, Android uniquement (`minSdk` par défaut de Flutter), testé sur émulateur seulement en M3.
- Paquets prévus (liste exacte confirmée à la tâche, voir « Ask first ») :
  - `swagger_parser` (dev) et `http`, seule dépendance du client qu'il génère (client `http`, modèles `plain`) ;
  - `flutter_secure_storage` (identifiant utilisateur), `shared_preferences` (thème, dernière ouverture), `url_launcher` (liens) ;
  - `flutter_launcher_icons` (dev, icône de l'app).
- Architecture : celle recommandée par Flutter (couches UI, logique, données) avec `ChangeNotifier` et `ListenableBuilder`, sans Riverpod ni Bloc. Navigation avec `Navigator`, sans `go_router`.

## Commands
Depuis `mobile/` :
```
Dépendances : flutter pub get
Schéma      : (cd ../backend && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))") > openapi.json
Client      : dart run swagger_parser
Analyse     : dart format --set-exit-if-changed . && flutter analyze
Tests       : flutter test
Lancer      : flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
Icônes      : dart run flutter_launcher_icons
```
Backend (depuis `backend/`) : commandes de M2, et `docker compose up -d --build` depuis la racine pour l'API et le worker.

## Project Structure
```
mobile/
  openapi.json               schéma figé, source du client
  swagger_parser.yaml        configuration du générateur
  pubspec.yaml
  assets/fonts/              Inter, Literata (.ttf)
  lib/
    main.dart                démarrage, thème, première route
    data/
      api/                   client généré (ne pas modifier)
      repositories/          drawers, feed, user : seuls points d'accès à l'API
      device_store.dart      identifiant, thème, dernière ouverture
    ui/
      core/                  theme.dart (tokens, ThemeData), drawer_icons.dart, widgets partagés
      onboarding/            vue + view model
      feed/                  pastilles, liste, cartes
      drawer/                création, détail
      paper/                 détail d'un papier
      settings/
  test/                      même arborescence que lib/
backend/                     changements de backend-m3 (services, migrations, tests)
```

## Code Style
Identifiants, commentaires et commits en anglais ; docs en français. `dart format` et les règles de `flutter_lints`. Un view model par écran, qui n'appelle que des repositories ; les widgets n'appellent jamais l'API. Les couleurs et les polices viennent toujours du thème, jamais de valeurs en dur dans un widget.
```dart
class FeedViewModel extends ChangeNotifier {
  FeedViewModel(this._feed);

  final FeedRepository _feed;
  final List<FeedPaper> papers = [];
  int? drawerId; // null = All
  bool loading = false;
  Object? error;

  Future<void> loadMore() async {
    if (loading) return;
    loading = true;
    notifyListeners();
    try {
      papers.addAll(await _feed.page(drawerId: drawerId, offset: papers.length));
      error = null;
    } catch (e) {
      error = e; // shown as an inline error with Retry
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}
```

## Testing Strategy
- **Backend** : pytest comme en M2. Priorités : conversion LaTeX (une table de cas, dont `{\O}`, `{\aa}`, `\"o`, et un nom sans accent laissé intact) ; migration de données des auteurs ; `name`/`icon` obligatoires et validés (`422`) ; `fetched_at` présent dans les deux feeds.
- **Mobile** : `flutter test`, sans réseau ni vrai backend. Les repositories sont remplacés par des faux en mémoire.
  - Tests unitaires des view models : pagination, filtre par tiroir, signal « New », erreurs et Retry, limite du plan (`403`).
  - Tests de widgets des écrans : états vide, chargement, erreur ; pastilles (All, filtre, rangée masquée avec un seul tiroir) ; création d'un tiroir (validation des champs).
  - Pas de tests « golden » (captures) en M3.
- **Bout en bout, à la main** : le parcours des critères de réussite sur un émulateur Android contre `docker compose up`.
- **CI** : un job Flutter (format, analyse, tests, client régénéré sans différence) s'ajoute au job backend.

## Boundaries
- **Always :** une branche et une PR par tâche, avec les commandes de test ; test qui échoue d'abord ; lint et tests avant chaque commit ; couleurs et polices tirées du thème ; contrastes WCAG AA et cibles tactiles d'au moins 48 dp ; chaque écran vu dans un aperçu de widget (dart-flutter) puis relu avec ui-ux-pro-max (règles UX et accessibilité, guide Flutter) et emil-design-eng (finitions) avant la PR ; régénérer le client après tout changement d'API ; reporter dans DECISIONS.md toute décision nouvelle.
- **Ask first :** toute dépendance Dart ou Python absente de la Tech Stack ; changer un contrat `/v1` au-delà de ce que décrit `backend-m3` ; modifier la palette, les polices ou le logo ; la liste des icônes des tiroirs ; ajouter un écran ou une fonction hors de cette spec.
- **Never :** modifier le code généré à la main ; une couleur ou une police en dur dans un widget ; du miel pour du texte sur fond clair ; une route qui change le plan ; un appel réseau dans les tests ; pousser ou merger sur `main` ; mettre des task IDs dans les commits, PR ou branches.

## Success Criteria
1. Installation neuve sur un émulateur Android, backend local lancé : premier lancement → création d'un tiroir (nom, icône, prompt) → le feed montre « Butine is reading the latest papers… », puis des papiers pertinents en ≤ 2 min après un tirer-pour-rafraîchir.
2. Avec 3 tiroirs (`set-plan … paid`) : All puis une pastille par tiroir (icône + nom), puis +. Toucher une pastille filtre le feed et affiche le texte du prompt ; dans All, chaque papier montre son ou ses tiroirs.
3. En `free`, la création d'un 2ᵉ tiroir affiche le message de limite ; après `set-plan … paid`, elle réussit.
4. Toucher un papier ouvre son détail ; « Read on arXiv » ouvre le papier dans le navigateur.
5. Supprimer un tiroir (appui long, confirmation) le retire des pastilles et du feed.
6. Les papiers arrivés depuis la dernière ouverture portent « New », et plus à l'ouverture suivante.
7. Thèmes clair et sombre conformes à BRAND.md, polices Inter et Literata, icône Butine sur l'écran d'accueil du téléphone.
8. Backend arrêté : chaque écran affiche une erreur avec « Retry », sans plantage ; « Retry » fonctionne une fois le backend relancé.
9. Plus aucun auteur avec une commande LaTeX dans `/v1/papers` (vérifié sur la base locale).
10. CI verte : lint et tests backend, format, analyse et tests Flutter, client régénéré identique.

## Décisions à reporter dans DECISIONS.md
- `/v1` modifié sur place tant qu'aucune app n'est publiée ; `/v2` seulement après la première publication.
- Un tiroir a un nom court et une icône monochrome choisie dans un jeu fermé ; pas de renommage en M3.
- Pastilles en haut du feed (All + tiroirs) au lieu d'une liste de tiroirs séparée.
- Interface en anglais.
- Signal « New » : papiers récupérés (`fetched_at`) depuis la dernière ouverture du feed, gardée sur l'appareil.
- Client Dart généré par swagger_parser depuis un schéma commité, vérifié en CI.

## Open Questions
- ~~**Dépendances générées par swagger_parser**~~ : tranché, `http` seul (voir DECISIONS.md, API).
