# Idée : veille scientifique personnalisée

## Le problème
Le volume de publications scientifiques explose et il y a beaucoup
de bruit. Suivre l'état de l'art d'un domaine demande des heures
chaque semaine. Les alertes par mots-clés ne suffisent plus : elles
ratent les papiers pertinents qui utilisent d'autres termes et
laissent passer ceux qui ne font que citer le mot.

## La solution
Une application sur iPhone et Android de veille scientifique.
L'utilisateur décrit ses centres d'intérêt en langage naturel (des
« prompts ») au lieu de mots-clés. L'application récupère les
nouveaux papiers des sources scientifiques et une IA ne garde que
ceux qui correspondent vraiment à chaque prompt.

Chaque prompt a son propre « tiroir » (son propre feed). Un feed
global regroupe en plus les papiers de tous les prompts.

## L'audience
- Ingénieurs R&D qui veulent suivre l'état de l'art chaque semaine
  sans y passer des heures.
- Doctorants et chercheurs d'une même niche. Ce sont de gros
  utilisateurs, mais ils paient rarement.

## La monétisation
L'application sera publiée sur les stores. Elle doit être rentable,
sans plus : couvrir ses coûts.
- Gratuit : 1 feed.
- Payant : 10 feeds ou plus.

## Les sources
On reste uniquement sur les papiers scientifiques, via RSS : pas
d'autre technologie et rien d'illégal pour le moment.

Pour commencer : arXiv et bioRxiv, justement pour avoir plusieurs
sources et voir les problèmes que ça pose (le même papier publié à
deux endroits, des formats différents…).

Les sources sont imposées : l'utilisateur ne peut ni les choisir
(rien à cocher ou décocher) ni en ajouter.

On ne garde les papiers que 30 jours pour le moment, on verra après.

## Parcours utilisateur
1. L'utilisateur crée des prompts en les écrivant librement
   (ex : « détection d'anomalies sur séries temporelles
   industrielles », « batteries à électrolyte solide »).
2. L'application récupère régulièrement les nouveaux papiers des
   sources du catalogue.
3. Quand un papier correspond à un prompt, il apparaît dans le
   tiroir de ce prompt et dans le feed global.

## Contenu d'un élément du feed
- Titre du papier
- Auteurs
- Nom de la source
- L'abstract (puis un résumé par IA plus tard)
- Un lien vers l'original

## Comptes
C'est une application où les gens ont leur compte. D'abord un compte
utilisateur sans gestion de mot de passe, le reste viendra plus tard.

## Démarche
Je veux y aller petit à petit, une fonctionnalité à la fois, en
gardant à l'esprit que l'application va évoluer. D'abord le backend
qui récupère les papiers par RSS. Ensuite une IA qui reconnaît les
papiers selon les prompts. Etc.

## Mon contexte
- Je débute : je ne connais pas encore le RSS et je n'ai pas choisi
  de langage ni de technologies. Je suis cependant bachelorisé en
  informatique et je m'adapte vite.
- Je suis sur EndeavourOS (Arch Linux).
- J'aimerais profiter de ce projet pour me familiariser avec des
  technologies utiles pour des gros projets, comme Docker (je
  connais), Kubernetes et d'autres stacks ou architectures.
  Propose-moi lorsque tu vois une possibilité de les intégrer et
  que c'est utile. Si c'est overkill, fais-le-moi savoir.
