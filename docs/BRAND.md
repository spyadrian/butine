# Marque — Butine

Résultat de l'entretien de marque du 2026-11-04. Idée : [IDEE.md](IDEE.md), décisions produit : [DECISIONS.md](DECISIONS.md).
Chaque choix a sa raison ; si la raison ne tient plus, le choix peut changer.

Ce document fixe l'intention et, depuis le 2026-11-04, les valeurs finales du logo, des couleurs (y compris l'erreur) et de la police du logotype ; depuis le 2026-11-07, la serif des papiers (Literata).

Fichiers du logo, guide d'usage et scripts de génération : dossier [`design/logo/`](../design/logo/) (`GUIDE.md` pour le détail). Brief et recherche : [`design/logo/BRIEF.md`](../design/logo/BRIEF.md).

## Pour qui
Les **ingénieurs R&D qui veulent suivre les dernières sorties** de leur domaine. Ce sont eux qui paient.
Les doctorants et chercheurs utilisent aussi l'app, mais la marque ne se règle pas sur eux. Raison : ce sont les ingénieurs qui financent l'app ; un outil bon pour eux le sera aussi pour la recherche.

## Promesse et ressenti
- **Promesse** : « C'est trié, tu n'as rien raté. »
- **Ressenti principal : le soulagement.** On ouvre Butine, on voit l'essentiel en quelques minutes, on referme. Raison : le problème de départ est le bruit et le temps perdu, pas le manque de contenu.
- **Ressenti secondaire : la curiosité**, en second plan. Elle vit dans le moment où un nouveau papier pertinent apparaît, jamais dans des mécaniques qui poussent à revenir.

## Personnalité
**Calme, fiable, précis, chaleureux.**

| Butine, c'est | Butine, ce n'est pas |
|---|---|
| Un outil qu'on ouvre le matin et qu'on referme rassuré | Un fil qu'on fait défiler sans fin |
| Sobre, avec une touche de chaleur | Froid et institutionnel |
| De l'IA qui travaille en coulisse | De l'IA mise en avant comme argument |
| Un signal rare quand il y a du nouveau | Des pastilles et des compteurs partout |

## Le nom et l'abeille
L'abeille qui butine va de fleur en fleur et ne ramène que le meilleur : c'est exactement le tri que fait l'app.
- **L'abeille est suggérée, jamais dessinée.** Pas de mascotte, pas d'abeille reconnaissable dans le logo. Raison : une abeille illustrée ferait gadget pour des ingénieurs qui attendent un outil sérieux.
- Forme retenue : **l'alvéole ouverte** (voir « Logo et icône »). Autres pistes explorées puis écartées : goutte rayée, b rayé, entonnoir, intersection, abeilles dessinées (voir `design/logo/BRIEF.md`).
- L'hexagone est le premier cliché de l'abeille (la recherche du brief l'a relevé). Il est assumé : l'ouverture et le grain le distinguent d'une simple alvéole. C'est aussi pourquoi la recherche d'antériorité compte avant les stores.

## Couleurs
**Un neutre chaud qui porte le calme, un jaune miel en signature.**

| Rôle | Intention | Clair | Sombre | Où |
|---|---|---|---|---|
| Fond | Blanc cassé chaud / anthracite chaud | Blanc cassé `#FAF6EE` | Nuit `#1C1815` | Partout |
| Texte | Anthracite chaud / blanc cassé | Anthracite `#2B2520` | Blanc cassé `#FAF6EE` | Partout |
| Neutres secondaires | Gris chauds pour les métadonnées, séparateurs, éléments inactifs | `#766C62` | `#A39A90` | Auteurs, source, dates |
| **Signature : jaune miel** | Un jaune qui tire vers le miel, pas un jaune citron | Miel `#F2A93B` (en aplat, avec texte anthracite) | Miel `#F2A93B` | Icône de l'app, écran de démarrage, stores ; dans l'app : le bouton principal et le signal « nouveau papier » |
| Miel profond | Le miel quand il doit tenir sur fond clair | `#B9781A` | — | Grain du logo sur clair ; éléments graphiques seulement, jamais du texte |
| Erreur : grenat | Rouge rosé sourd, distinct du miel, jamais vif | `#A23B4E` (fond `#F7E7E6`) | `#E97F86` (fond `#3A2326`) | Messages d'erreur, champs invalides ; toujours avec une icône et un texte, jamais la couleur seule |

Contrastes vérifiés (WCAG) :
- anthracite sur blanc cassé : 14,0:1 ;
- anthracite sur miel : 7,6:1 ;
- blanc cassé sur nuit : 16,4:1 ;
- miel sur nuit : 8,8:1 ;
- gris `#766C62` sur blanc cassé : 4,8:1 ;
- gris `#A39A90` sur nuit : 6,4:1 ;
- miel profond sur blanc cassé : 3,4:1 (éléments graphiques uniquement) ;
- grenat `#A23B4E` sur blanc cassé : 6,0:1, et sur son fond `#F7E7E6` : 5,4:1 ;
- grenat sombre `#E97F86` sur nuit : 6,6:1, et sur son fond `#3A2326` : 5,4:1 ;
- miel sur blanc cassé : 1,9:1, **interdit** pour le texte, les icônes et le logo.

Équivalents RGB et CMJN : voir `design/logo/GUIDE.md`. Aperçu de la palette en situation : `design/logo/presentation/lockups-couleurs.png`.

Pourquoi un grenat pour l'erreur : sa teinte (rouge rosé, vers 350°) est loin de celle du miel (orangé, vers 36°), donc on ne confond pas l'erreur avec la signature. Il est assez sourd pour ne pas devenir une alerte criarde. En vision deutéranope (simulée), le miel reste jaune et le grenat devient un brun-gris plus foncé : les deux restent distincts par leur luminosité.

Règles :
- **Le jaune est rare dans l'app.** Il domine les moments de marque, mais dans l'interface il ne marque que ce qui compte. Raison : utilisé partout, il casse le calme et devient « panneau de chantier » ; utilisé rarement, il devient le signal « il y a quelque chose pour toi », qui porte la curiosité.
- **Jamais de jaune pour du texte ou de petites icônes sur fond clair.** Raison : contraste insuffisant. Sur un fond jaune, le texte est anthracite.
- **Le jaune ne sert pas aux avertissements**, et les erreurs ont leur propre couleur, distincte. Raison : en interface, le jaune veut souvent dire « attention » ; on évite toute confusion avec la signature.
- **Pas de rouge vif pour attirer l'attention** (pastilles, compteurs). Raison : contredit le soulagement.
- Pas de dégradés, pas d'effets de verre dépoli.

## Typographie
**Un mélange : sans-serif pour l'interface, serif lisible pour le contenu.**
- **Sans-serif** : boutons, menus, onglets, métadonnées. Nette et neutre.
- **Serif** : titres et abstracts des papiers. Raison : sépare visuellement l'outil (l'interface) de la science qu'on lit, donne de la personnalité sans faire daté, et aide à lire de longs abstracts sur mobile.
- Critères de choix : gratuites et utilisables dans une app (licence OFL, Google Fonts par exemple), bon rendu en petite taille sur mobile, plusieurs graisses, et les deux polices doivent s'accorder (hauteurs, rythme).
- **Logotype** : Adwaita Sans SemiBold (600), taille optique 32, interlettrage −1,2 %, converti en tracés. Adwaita Sans est une version d'Inter, sous licence SIL OFL 1.1. On ne retape jamais « Butine » pour reproduire le logo : on utilise les fichiers SVG.
- **Sans-serif de l'interface** : Inter est le choix naturel, puisqu'elle accorde l'interface au logotype. Confirmée dans le code (M3, `mobile/lib/ui/core/theme.dart`).
- **Serif des papiers : Literata** (Google Fonts, SIL OFL 1.1), pour les titres et les abstracts. Raison : dessinée pour la lecture longue sur écran, chaleureuse sans faire d'effet ; c'est la plus lisible des quatre comparées sur un vrai abstract à largeur de téléphone (Source Serif 4, plus neutre ; Newsreader, plus fine ; Fraunces, plus marquée et plus à la mode).

## Ton de voix
- Phrases courtes et concrètes. On dit ce qui se passe (« 3 nouveaux papiers ») sans enthousiasme forcé.
- On ne vante pas l'IA ; on montre le résultat.

## Logo et icône
**Symbole : l'alvéole ouverte.** Un hexagone à pointe en haut, dessiné d'un seul trait, dont le côté haut-droit est ouvert. Un grain de pollen se pose dans l'ouverture : c'est le tri, seul le grain qui compte entre. Raison : l'abeille est suggérée (alvéole et pollen) sans être dessinée, et la forme reste simple et lisible en icône.
- **Construction** : trait de 26 unités sur une grille de 256, angles de 60°, coins arrondis, grain de Ø 34. Le point du « i » du logotype répond au grain.
- **Coupes par taille** : standard au-dessus de 32 px ; `symbol-small` de 24 à 32 px ; `symbol-tiny` à 16–23 px (favicons), avec des extrémités raccourcies et un grain plus gros pour que l'ouverture reste visible.
- **Couleurs du logo**
  - sur clair : anthracite, ou anthracite avec grain miel profond en grand format ;
  - sur sombre : blanc cassé avec grain miel ;
  - sur miel : anthracite ;
  - en une couleur : noir ou blanc.
- **Icône d'app** : symbole anthracite sur fond miel. iOS reçoit un carré plein sans transparence ; Android une icône adaptative (avant-plan, arrière-plan, monochrome).
- **Lockups** : horizontal (version principale), empilé (écran de démarrage, stores), symbole seul, logotype seul.
- **Zone de protection** : un diamètre de grain tout autour.
- **Tailles minimales** : horizontal 96 px, symbole 24 px (16 px avec la coupe tiny).
- **Interdits** : refermer l'alvéole ou déplacer le grain, déformer ou faire pivoter, ajouter un dégradé, une ombre ou un contour, poser du miel sur fond clair.
- **Avant les stores** : faire une recherche d'antériorité (IPI, EUIPO, recherche d'image inversée).

## À éviter
- **Le look « startup IA »** : dégradés violet-bleu, étincelles ✨, verre dépoli, « powered by AI ».
- **Le look « académique »** : bleu institutionnel terne, interface dense et datée.
- **Le look « réseau social »** : couleurs criardes, notifications rouges, compteurs et pastilles qui poussent à revenir.

## Contraintes
- **Accessibilité** : contrastes conformes à WCAG AA (4,5:1 pour le texte courant, 3:1 pour le gros texte et les éléments d'interface), en clair comme en sombre.
- **Mode sombre dès le départ** : chaque couleur a sa version claire et sa version sombre.
- **Polices gratuites** et autorisées dans une app publiée.
- **Fait en code, pas dans Figma** : les explorations (palette, typo, logo en SVG) sont faites et vérifiées directement dans le code.

## Hors périmètre (pour l'instant)
Écrans de l'app, landing page web, code Flutter (`ThemeData`), mascotte, visuels des stores.

## Prochaines étapes
1. ~~Logo, couleurs de marque, police du logotype~~ : faits le 2026-11-04 (voir plus haut).
2. ~~Serif des papiers~~ : Literata, choisie le 2026-11-07 (voir « Typographie »).
3. **Spec du design system** : tokens (à partir de `design/logo/palette.json`) puis `ThemeData`, le pont vers les écrans de M3.
4. **Moodboard** : inspirations Mobbin pour les écrans, confrontées à ce brief.
5. **Recherche d'antériorité** de la marque avant la publication sur les stores.
