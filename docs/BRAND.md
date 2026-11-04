# Marque — Butine

Résultat de l'entretien de marque du 2026-11-04. Idée : [IDEE.md](IDEE.md), décisions produit : [DECISIONS.md](DECISIONS.md).
Chaque choix a sa raison ; si la raison ne tient plus, le choix peut changer.

Ce document fixe l'intention. Les valeurs exactes (codes couleur, polices, logo) sont choisies à l'étape suivante, en les testant dans le code contre les règles ci-dessous.

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
- Pistes de formes abstraites : alvéole, trajectoire de vol d'une fleur à l'autre, grain de pollen, goutte de miel.

## Couleurs
**Un neutre chaud qui porte le calme, un jaune miel en signature.**

| Rôle | Intention | Où |
|---|---|---|
| Fond | Blanc cassé chaud (clair) / anthracite chaud (sombre) | Partout |
| Texte | Anthracite chaud (clair) / blanc cassé (sombre) | Partout |
| Neutres secondaires | Gris chauds pour les métadonnées, séparateurs, éléments inactifs | Auteurs, source, dates |
| **Signature : jaune miel** | Un jaune qui tire vers le miel, pas un jaune citron | Icône de l'app, écran de démarrage, stores ; dans l'app : le bouton principal et le signal « nouveau papier » |

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

## Ton de voix
- Phrases courtes et concrètes. On dit ce qui se passe (« 3 nouveaux papiers ») sans enthousiasme forcé.
- On ne vante pas l'IA ; on montre le résultat.

## Logo et icône
- Une forme abstraite qui évoque l'abeille (voir plus haut), lisible à la taille d'une icône d'app sur l'écran d'accueil.
- Fonctionne en une seule couleur (anthracite sur clair, blanc cassé sur sombre) et sur le fond jaune miel de l'icône.
- Un logotype « Butine » à côté du symbole, pour les stores et l'écran de démarrage.

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
1. **Moodboard** : inspirations Mobbin confrontées à ce brief.
2. **Explorations en code** : nuances de jaune miel (contraste vérifié), neutres chauds, paires de polices, pistes de logo en SVG.
3. **Spec du design system** : tokens puis `ThemeData`, le pont vers les écrans de M3.
