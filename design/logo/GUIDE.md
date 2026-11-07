# Butine : guide d'usage du logo

Ce guide tient en une page et s'adresse aussi aux non-designers. Le brief et la recherche sont dans [BRIEF.md](BRIEF.md), la marque dans `docs/BRAND.md`.

## 1. Le logo
- **Idée** : une alvéole ouverte où n'entre que le grain qui compte. C'est le tri que fait l'app (« C'est trié, tu n'as rien raté »). L'abeille est suggérée, jamais dessinée.
- **Construction** : un hexagone à pointe en haut, dessiné d'un seul trait de 26 unités (sur une grille de 256), avec des angles de 60°. Le côté haut-droit est ouvert. Le grain (Ø 34) se pose au milieu de ce côté ouvert. Le point du « i » du logotype répond au grain.
- **Versions**
  - horizontal (version principale) : `butine-horizontal-*.svg`
  - empilé, pour l'écran de démarrage et les stores : `butine-empile-*.svg`
  - symbole seul : `symbol-*.svg`
  - logotype seul : `butine-logotype-*.svg`
- **Coupes par taille** : `symbol-*.svg` au-dessus de 32 px ; `symbol-small.svg` de 24 à 32 px ; `symbol-tiny.svg` à 16–23 px (favicons). La version tiny a des extrémités raccourcies et un grain plus gros, pour que l'ouverture reste visible.

## 2. Zone de protection
Autour du logo, garde une marge libre d'**au moins un diamètre de grain** de chaque côté. Cette marge suit la taille du logo : ce n'est jamais une distance fixe.

## 3. Tailles minimales
| Version | Écran | Impression |
|---|---|---|
| Horizontal | 96 px de large | 25 mm de large |
| Empilé | 64 px de large | 18 mm de large |
| Symbole | 24 px (`symbol-small`) ; 16 px avec `symbol-tiny` | 6 mm |

## 4. Couleurs
| Nom | Rôle | HEX | RGB | CMJN (approx.) |
|---|---|---|---|---|
| **Miel** | Signature : icône, démarrage, bouton principal, signal « nouveau » | `#F2A93B` | 242 169 59 | 0 30 76 5 |
| Miel profond | Grain du logo sur fond clair | `#B9781A` | 185 120 26 | 0 35 86 27 |
| Anthracite | Logo et texte sur clair | `#2B2520` | 43 37 32 | 0 14 26 83 |
| Blanc cassé | Fond clair ; logo sur sombre | `#FAF6EE` | 250 246 238 | 0 2 5 2 |
| Nuit | Fond sombre | `#1C1815` | 28 24 21 | 0 14 25 89 |
| Gris chaud clair | Métadonnées sur clair | `#766C62` | 118 108 98 | 0 8 17 54 |
| Gris chaud sombre | Métadonnées sur sombre | `#A39A90` | 163 154 144 | 0 6 12 36 |
| Erreur (grenat) | Erreurs sur clair ; fond `#F7E7E6` | `#A23B4E` | 162 59 78 | 0 64 52 36 |
| Erreur, sombre | Erreurs sur sombre ; fond `#3A2326` | `#E97F86` | 233 127 134 | 0 45 42 9 |

Les valeurs CMJN sont converties mathématiquement. Pour un vrai tirage, il faut les vérifier sur épreuve et choisir le Pantone à l'aide d'un nuancier.

**Contrastes vérifiés (WCAG)**
- anthracite sur blanc cassé : 14,0:1
- anthracite sur miel : 7,6:1
- blanc cassé sur nuit : 16,4:1
- miel sur nuit : 8,8:1
- gris clair sur blanc cassé : 4,8:1
- gris sombre sur nuit : 6,4:1
- miel profond sur blanc cassé : 3,4:1. Ce n'est valable que pour un élément graphique : jamais pour du texte.
- **Le miel sur fond clair (1,9:1) est interdit**, aussi bien pour le logo que pour le texte ou les petites icônes.

**Fonds et couleurs autorisés**
| Fond | Logo |
|---|---|
| Clair (blanc cassé ou blanc) | anthracite. La version `-miel`, avec le grain miel profond, reste possible en grand. |
| Miel | anthracite (c'est l'icône d'app) |
| Sombre (nuit) | `-inverse` : blanc cassé avec grain miel |
| Photo | blanc ou noir, sur une zone calme |

## 5. Typographie
- **Logotype** : Adwaita Sans SemiBold (600), taille optique 32, interlettrage −1,2 %, converti en tracés. Adwaita Sans est une version d'Inter, sous licence SIL OFL 1.1. Pour que le logo marche, il n'est pas nécessaire d'installer la police.
- **Interface** : la sans-serif de l'app pourra être Inter, qui va naturellement avec le logotype. La serif des titres et abstracts des papiers est Literata (voir BRAND.md).
- On ne retape jamais « Butine » au clavier pour reproduire le logo : on utilise les fichiers SVG.

## 6. À ne pas faire
- déformer, incliner ou faire pivoter le logo ;
- refermer l'alvéole ou déplacer le grain ;
- mettre le grain dans une autre couleur que l'anneau, sauf dans les versions `-miel` et `-inverse` ;
- ajouter un dégradé, une ombre, un contour ou du verre dépoli ;
- poser du miel sur fond clair ;
- utiliser le miel comme couleur d'avertissement dans l'app ;
- changer les proportions entre le symbole et le logotype ;
- poser le logo sur un fond chargé sans cartouche.

## 7. Fichiers
| Dossier / fichier | Contenu |
|---|---|
| `symbol-*.svg`, `butine-*.svg` | Masters vectoriels (tracés pleins, pas de texte) |
| `exports/app/icon-ios-1024.png` | App Store (carré plein, sans transparence ; iOS arrondit lui-même) |
| `exports/app/android-{foreground,background,monochrome}-*.{svg,png}` | Icône adaptative Android ; monochrome pour les icônes thémées d'Android 13+ |
| `exports/web/` | favicon.ico, favicon.svg, apple-touch-icon, icon-192/512, maskable, site.webmanifest, `head-snippet.html` |
| `presentation/lockups-couleurs.png` | Tous les lockups sur leurs fonds, coupes par taille, palette, erreur en situation (`build_sheet.py`) |
| `build_symbol.py`, `build_wordmark.py`, `build_lockups.py`, `palette.json` | Sources : modifier `palette.json` ou les paramètres, puis relancer les scripts |

## 8. Points ouverts
- **Recherche d'antériorité** de la marque et du symbole (IPI suisse, EUIPO, recherche d'image inversée) avant la publication sur les stores. Les hexagones sont fréquents dans la tech.
- Mettre à jour `docs/BRAND.md` avec les valeurs exactes (couleurs, police du logotype).
- Si le miel profond sert aussi dans l'interface, il faudra de nouveau vérifier ses contrastes dans le code Flutter.
