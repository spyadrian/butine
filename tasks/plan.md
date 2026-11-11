# Plan d'implémentation : jalon M3 — app Flutter minimale

## Vue d'ensemble
M3 livre une app Android (émulateur seulement) où l'utilisateur crée ses tiroirs (nom, icône, prompt) et lit ses papiers, tous ensemble dans All ou tiroir par tiroir grâce aux pastilles, avec l'identité de BRAND.md. Le backend gagne trois changements (auteurs sans LaTeX, `name`/`icon` sur les prompts, `fetched_at` sur les papiers) ; l'app parle à l'API par un client Dart généré.
Référence : [docs/SPEC.md](../docs/SPEC.md) (contrats, écrans, règles, critères de réussite), [docs/BRAND.md](../docs/BRAND.md), [docs/DECISIONS.md](../docs/DECISIONS.md). Ce plan n'y ajoute que l'ordre des tâches et quelques choix d'implémentation.

## Choix d'implémentation (nouveaux, à valider)
| Choix | Raison |
|---|---|
| Numérotation qui continue celle de M2 (T20 → T34) | « T3 » ne peut pas désigner deux tâches différentes en discussion. |
| Les trois changements backend d'abord (T20 → T22) | La correction LaTeX passe en premier, comme décidé. Le schéma de l'API est ainsi final avant de générer le client une seule fois (T25), au lieu de le régénérer après chaque changement. |
| Le squelette Flutter et sa CI (T23) avant tout écran | C'est le premier contact avec Flutter dans le repo : s'il y a un problème d'outillage (Android SDK, émulateur, CI), on le voit sur une tâche minuscule. |
| Le client généré (T25) est une tâche à part, tôt | C'est le risque principal côté mobile : swagger_parser doit produire un client qui compile depuis le schéma FastAPI. La liste exacte des dépendances (question ouverte de la spec) y est tranchée. |
| Un test Dart qui calcule les contrastes des tokens (T24) | Les ratios WCAG de BRAND.md restent vrais même si quelqu'un touche une couleur plus tard. Quelques lignes, aucune dépendance. |
| Écrans en tranches verticales (T27 → T34) | Chaque tâche livre un morceau du parcours qu'on peut lancer sur l'émulateur : repository + view model + écran + tests. |
| Chaque décision est reportée dans DECISIONS.md par la tâche qui l'applique | Pas de tâche « documentation » en fin de jalon, que l'on oublie. |
| Chaque tâche d'écran passe par l'aperçu de widget, ui-ux-pro-max et emil-design-eng avant sa PR | Règle de la spec (« Always ») ; c'est là que le rendu visuel se décide. |

## Graphe de dépendances
```
T20 auteurs sans LaTeX
T21 name + icon sur les prompts ─────┐
T22 fetched_at sur les papiers ──────┤
T35 auteurs arXiv sans affiliations  │
T23 squelette Flutter + CI ──────────┼── T25 client API généré
 ├── T24 thème, tokens, polices      │          │
 │    └── T26 icônes (tiroirs, app)  │          │
 │                                   │          │
 └───────────────────────────── T27 identité + premier lancement
                                     └── T28 création d'un tiroir (T26)
                                          └── T29 feed All
                                               ├── T30 pastilles + feed d'un tiroir
                                               │    └── T33 détail d'un tiroir + suppression
                                               ├── T31 signal « New »
                                               └── T32 détail d'un papier
T24 ── T34 réglages + choix du thème
```
T20 et T35 sont indépendantes de tout le reste. T24 et T25 sont indépendantes une fois T23 faite.

## Liste des tâches
Détail (critères, vérifications, fichiers) dans [todo.md](todo.md).

### Phase 1 : backend
- [x] T20 : auteurs sans commandes LaTeX (parseur + migration de données)
- [x] T21 : `name` et `icon` sur les prompts
- [x] T22 : `fetched_at` dans les papiers
- [x] T35 : auteurs arXiv sans affiliations (parseur + migration de données)

### Checkpoint 1
- [x] Lint + tests backend passent, CI verte
- [x] `/v1/papers` ne renvoie plus d'auteur avec une commande LaTeX ni avec une affiliation sur la base locale
- [x] Revue humaine

### Phase 2 : socle mobile
- [x] T23 : projet Flutter Android dans `mobile/` + job CI
- [x] T24 : thème (tokens, polices, clair/sombre)
- [x] T25 : client API généré par swagger_parser, vérifié en CI
- [x] T26 : jeu d'icônes des tiroirs + icône de l'app

### Checkpoint 2
- [x] L'app se lance sur l'émulateur, aux couleurs et polices de Butine, avec son icône
- [x] CI verte (backend + mobile, client régénéré identique)
- [x] Revue humaine (dont la liste des icônes des tiroirs)

### Phase 3 : parcours principal
- [x] T27 : identité de l'appareil + premier lancement
- [x] T28 : création d'un tiroir
- [x] T29 : feed All (liste, pagination, rafraîchir, états)
- [x] T30 : pastilles + feed d'un tiroir
- [x] T31 : signal « New »

### Checkpoint 3
- [ ] Critères de réussite 1, 2, 3 et 6 de la spec, à la main sur l'émulateur
- [ ] Revue humaine

### Phase 4 : compléments
- [ ] T32 : détail d'un papier
- [ ] T33 : détail d'un tiroir + suppression
- [ ] T34 : réglages + choix du thème

### Checkpoint final
- [ ] Tous les critères de réussite de docs/SPEC.md remplis
- [ ] Décisions de la spec reportées dans DECISIONS.md
- [ ] CI verte
- [ ] Revue humaine avant la suite (compte anonyme, paiement)

## Risques et mitigations
| Risque | Impact | Mitigation |
|---|---|---|
| swagger_parser produit un client qui ne compile pas ou mal typé depuis le schéma FastAPI (nullables, `list[str]`, UUID) | Haut | T25 tôt et isolée. Si le schéma pose problème, on l'ajuste côté FastAPI (noms d'opérations, types) plutôt que de retoucher le code généré. Repli : openapi-generator, à décider ensemble. |
| L'outillage Android (SDK, émulateur, Gradle) ou le job Flutter en CI casse | Moyen | T23 ne fait que ça ; `flutter doctor` est vert et l'émulateur existe déjà. |
| La migration de données LaTeX abîme des noms d'auteurs | Moyen | Fonction pure testée sur une table de cas, dont des noms sans accent laissés intacts ; la migration réutilise cette même fonction. |
| Le feed global reste vers 150 ms et l'app enchaîne les appels (pagination, pastilles) | Faible | Volumes locaux ; la table `matches` de DECISIONS.md reste le recours. On mesure au Checkpoint 3. |
| HTTP en clair refusé par Android en debug | Faible | Autorisé en debug seulement, dans le manifeste de debug (T23). |
| Le design visuel s'éternise tâche après tâche | Moyen | Le rendu se décide dans la tâche de l'écran, relu par les skills ; les retouches globales attendent le Checkpoint 3. |

## Open Questions
- Aucune nouvelle. La question de la spec (dépendances du client généré) est tranchée dans T25.
