# KatieCAD – Guide rapide (français)

> Version allemande : [ANLEITUNG.md](ANLEITUNG.md) · Version anglaise originale : [USER_GUIDE.md](USER_GUIDE.md)

KatieCAD est un programme de CAO 2D avec une extension d'électrotechnique. Ce guide
montre où trouver les fonctions de base. Il sert de rappel si vous n'avez pas utilisé
le programme depuis un moment, ou si vous le découvrez.

## Sommaire

1. [Démarrage](#1-démarrage)
2. [La fenêtre en un coup d'œil](#2-la-fenêtre-en-un-coup-dœil)
3. [Navigation, accrochage, ligne de commande](#3-navigation-accrochage-ligne-de-commande)
4. [Dessin et édition](#4-dessin-et-édition)
5. [Projets et feuilles](#5-projets-et-feuilles)
6. [Modèle, présentation, cadre, impression](#6-modèle-présentation-cadre-impression)
7. [Blocs et attributs](#7-blocs-et-attributs)
8. [Électricité : dessiner un schéma](#8-électricité--dessiner-un-schéma)
9. [Générer la documentation](#9-générer-la-documentation)
10. [Import et export](#10-import-et-export)
11. [Raccourcis clavier](#11-raccourcis-clavier)
12. [Astuces et questions fréquentes](#12-astuces-et-questions-fréquentes)

---

## 1. Démarrage

```
python main.py
```

ou `python -m katiecad`. Installez éventuellement les paquets supplémentaires avec
`pip install -r requirements.txt` (nécessaires pour l'import DXF/DWG et l'export DXF). Sous Linux,
il faut en plus `python3-tk`.

Changez la langue dans le menu **Paramètres > Langue** (Deutsch / English / Español). Elle est mémorisée.

## 2. La fenêtre en un coup d'œil

| Zone | Ce qu'elle fait |
|---|---|
| **Barre de menus** | Fichier, Projet, Édition, Insertion, Affichage, Blocs, Électricité, Paramètres, Aide |
| **Barres d'outils** (une pour les outils, une pour l'électricité et une pour la 3D, librement plaçables) | Outils de dessin (Sélectionner, Ligne, Polyligne, Cercle, Arc, Rectangle, Texte, Cotation, Ajuster, Rupture) et les outils électriques (Broche, Jonction, Renvoi, Masque, Borne, Câble, …). Aussi calque, type de ligne, épaisseur de trait, couleur, unité, échelle et zoom. |
| **Panneau latéral** (à gauche, F4 l'affiche ou le masque) | Annuler / Rétablir et la liste des feuilles du projet |
| **Zone de dessin** | C'est là que vous dessinez. Le modèle est le dessin à l'échelle 1:1, la présentation est la feuille de papier. |
| **Ligne de commande** | Sous la zone de dessin. Saisissez-y les commandes et les coordonnées. |
| **Barres d'outils** | Les outils de dessin sont violets, les outils électriques rouges ; le zoom a des icônes en forme de loupe (+, −, « + G » = zoom étendu) et une icône de réinitialisation. |
| **Barre d'état** | Coordonnées de la souris, zoom, calque, sélection, messages de l'outil courant et les commutateurs d'accrochage aux objets, de grille et d'ortho |

L'indication de la barre d'état dit toujours ce que l'outil actif attend ensuite.
**Échap** annule l'opération en cours.

## 3. Navigation, accrochage, ligne de commande

**À la souris**

- Molette de la souris : zoom (vers le pointeur).
- Maintenir le bouton droit et faire glisser : déplacer la vue (panoramique).
- Clic droit sans glisser (outil « Sélectionner ») : menu contextuel.
- Double-clic avec le bouton du milieu ou le bouton droit : tout afficher (zoom étendu).
  La touche **G** produit le même effet.

**Accrochage et aides** (commutateurs de la barre d'état, aussi disponibles au clavier)

| Touche | Fonction |
|---|---|
| F3 | Accrochage aux objets (extrémité, milieu, centre, intersection — aussi ligne × cercle/arc et cercle × cercle —, quadrant, perpendiculaire, le plus proche) |
| F7 | Afficher la grille |
| F8 | Ortho (horizontal / vertical uniquement) |
| F9 | Accrochage à la grille |

**Ligne de commande.** Vous pouvez saisir des coordonnées sous la forme `x,y` et taper des commandes, par exemple
`L` (ligne), `K` (cercle), `REC` (rectangle), `T` (texte), `M` (déplacer), `KO` ou `CO`
(copier), `RO` (rotation), `AR` (réseau), `STR` (étirer), `TR` (ajuster), `BR` (rupture),
`ZG` (zoom étendu), `U` (annuler), `B` (créer un bloc), `I` (insérer un bloc),
`X` (décomposer un bloc). Les commandes existent en allemand et en anglais.

## 4. Dessin et édition

1. Choisissez un outil (barre d'outils ou menu **Insertion**), cliquez des points dans le dessin ou tapez
   des coordonnées dans la ligne de commande.
2. Avec l'outil **Sélectionner**, vous sélectionnez des objets : cliquez sur un objet ou faites glisser un
   rectangle. *De gauche à droite*, seuls les objets entièrement à l'intérieur du
   rectangle sont sélectionnés. *De droite à gauche*, tout ce que le rectangle touche. Les nouveaux objets
   s'ajoutent à la sélection ; **Échap** la vide.
3. Modifiez les objets sélectionnés via le menu **Édition** : copier, couper, coller, dupliquer, déplacer,
   copier avec point de base, rotation, étirer, réseau, supprimer (Suppr).
4. Faites glisser les poignées jaunes d'un objet sélectionné pour le modifier.
5. Un double-clic sur un objet ouvre sa boîte de dialogue d'édition (attributs de bloc, broche, renvoi,
   jonction, masque, borne, câble, champ de coordonnées …). Sur une fenêtre de vue, il
   active la fenêtre de vue.
6. **Annuler** (Ctrl+Z) et **Rétablir** (Ctrl+Y) sont aussi dans le panneau latéral.

Autres aides au dessin : **cotations** (y compris rayon et diamètre), **sélection de
hachures** (menu Insertion), **calques** (bouton « Calques… ») et couleur, type de ligne et
épaisseur de trait dans la barre d'outils.

**Rechercher et remplacer (Ctrl+F, Édition > Rechercher et remplacer, commande `FIND`) :** saisissez le texte recherché et le nouveau texte, et choisissez la portée *Feuille courante*, *Projet entier* ou **Sélection seulement** (recherche et remplace uniquement dans les objets préalablement sélectionnés ; si quelque chose est sélectionné à l'ouverture de la fenêtre, la portée est déjà réglée sur celle-ci). KatieCAD liste toutes les occurrences avec leur feuille, leur type d'objet et leur champ, et affiche le nouveau texte à côté. Il recherche dans les textes, les textes de cotation, les renvois, les masques (IND/TYP/PER ...), les bornes, les câbles, les broches et les attributs de bloc (donc aussi la désignation des appareils). **Double-cliquez sur une occurrence** pour aller à l'objet : KatieCAD ouvre la feuille si nécessaire, sélectionne l'objet et zoome dessus ; la fenêtre de recherche reste ouverte et se décale. En option : respecter la casse, mots entiers seulement. *Remplacer la sélection* ne modifie que les lignes surlignées, *Tout remplacer* les modifie toutes. Les modifications de la feuille ouverte peuvent être annulées par Ctrl+Z ; celles des autres feuilles sont enregistrées immédiatement et ne peuvent pas y être annulées (KatieCAD demande d'abord).

**Reproduire les propriétés (Édition > Reproduire les propriétés, commande `MA`) :** cliquez d'abord sur l'objet source, puis sur les objets cibles l'un après l'autre. Calque, couleur, type de ligne et épaisseur de trait sont copiés ; pour les textes, aussi la hauteur et la police ; pour les hachures, l'angle et l'espacement. Échap ou un clic droit termine.

**Écriture normalisée (polices « ISO » et « ISO italique ») :** police à trait unique intégrée à KatieCAD, calquée sur ISO 3098 / DIN 6776 (type B) : capitales 10/10 h, bas de casse 7/10 h avec jambages 3/10 h, épaisseur du trait 1/10 h (gras : 1,5/10 h), espacement des lettres et des mots comme dans la norme ; la variante oblique est inclinée de 15 degrés. Choisissez-la comme toute autre police dans la liste de polices de la barre d'outils, la boîte de dialogue texte, les propriétés, pour les cotations et les locaux, et dans la boîte de dialogue de documentation pour toutes les feuilles de rapport. Elle n'a pas besoin d'être installée et rend pareil sur chaque ordinateur, à l'écran comme dans le PDF (les traits sont dessinés comme des lignes, donc aucun fichier de police n'est nécessaire). Elle contient A-Z, a-z, 0-9, les trémas et le ß, Ø ø Ω µ ° ± ² ³ € ainsi que la ponctuation et les caractères mathématiques usuels ; les caractères manquants apparaissent comme un petit carré. Remarque : la police est un dessin original suivant les proportions de la norme, pas un modèle officiel de la norme. **Export DXF (Paramètres > Export DXF de la police ISO) :** *En texte* écrit des textes DXF normaux avec le style de texte « ISO » (fichier de police `isocp.shx`, disponible dans AutoCAD et BricsCAD ; aspect, largeur et inclinaison peuvent différer légèrement) — le texte y reste modifiable. *En lignes* écrit chaque trait comme polyligne : aspect identique dans tous les programmes, mais ce n'est plus du texte et le fichier grossit. Le choix est mémorisé.

**Polices personnelles (Paramètres > Gérer les polices...) :** choisissez une police installée sur cet ordinateur (TrueType/OpenType) ; elle apparaît ensuite à côté des sept polices standard dans la liste de polices de la barre d'outils, de la boîte de dialogue texte et des propriétés. Le choix est enregistré ; pour **retirer** une police, décochez-la dans la même fenêtre (« Sélectionnées seulement » n'affiche que les actives, « Tout désélectionner » vide la liste). La largeur du texte est calculée avec les largeurs réelles de la police, et le **PDF incorpore les polices** (lisible sur des ordinateurs sans la police). Les polices marquées « (écran seulement) » (par ex. OTF à contours CFF) ou soumises à une restriction d'incorporation apparaissent en Helvetica dans le PDF. Si vous ouvrez un dessin qui utilise une police installée ici mais non choisie, elle est activée automatiquement pour la session ; si elle manque totalement, KatieCAD affiche une police de substitution. La police à trait des textes 3D n'est pas concernée.

**Thème de couleurs (Paramètres > Thème de couleurs) :** menus, barres d'outils, panneaux latéraux et boîtes de dialogue existent en trois thèmes : **Violet** (par défaut), **Noir** et **Clair**. Le changement s'applique aussitôt et est mémorisé pour le prochain démarrage. Le fond du dessin n'est pas touché (réglez-le avec *Fond*, en choisissant alors un fond clair). **Le fond (modèle et présentation) est purement un réglage du programme :** il est stocké sur votre ordinateur et non plus dans le fichier de dessin ou de projet ; un fichier enregistré par quelqu'un avec un fond blanc s'ouvre avec votre propre fond (les anciens fichiers sont lus de la même façon, leur fond enregistré est ignoré) ; le contenu du dessin, les calques et la sortie imprimée/PDF ne changent pas. Les boîtes de dialogue déjà ouvertes prennent le nouveau thème à leur prochaine ouverture.

**Fond du dessin (Paramètres > Fond du modèle... / Fond de la présentation...) :** règle la couleur de fond du modèle ou de la vue de présentation — librement choisie ou via le champ **Prédéfini** (Défaut, Blanc/papier, Noir, Gris foncé, Gris clair, Bleu, Beige) (mémorisé dans le programme, s'applique à tous les dessins).

**Couleur de la grille (Paramètres > Couleur de la grille... / Réinitialiser la couleur de la grille ; depuis 1.1.6) :** règle la couleur de la grille dans la zone du modèle. Dans la barre du bas, à côté de *Fond*, il y a le champ de couleur *Grille :* et une liste (Défaut, Violet, Gris, Bleu, Vert, Rouge, Orange, Blanc, Noir) ; *Défaut* restaure la couleur d'origine de la grille. Points et lignes secondaires et principales sont composés de la couleur choisie et du fond, de sorte que la grille reste discrète sur fond clair comme sur fond sombre. Le choix est mémorisé dans le programme et s'applique à tous les dessins.

**Afficher la vitesse de dessin (Paramètres ; depuis 1.1.6) :** après chaque redessin, la barre d'état indique le temps pris par le calcul du modèle, les éléments et la grille, ainsi que le nombre d'éléments et d'objets. Utile pour trouver les goulots d'étranglement dans les grands dessins ; non enregistré.

**Barre d'outils :** les outils sont des icônes (dessin en violet, électricité en rouge). Laissez la souris sur une icône pour voir son nom. L'outil actif a un fond plus clair.

**Décalage (Édition > Décalage, commandes `OFFSET` / `O`) :** saisissez la distance, cliquez sur un objet, puis cliquez du côté où la copie doit être créée. Fonctionne avec les lignes, cercles, arcs, rectangles et polylignes (les angles sont traités en onglet). Si la distance est trop grande (vers l'intérieur), KatieCAD affiche « impossible ».

**Modifier la longueur (Édition > Modifier la longueur, barre d'outils, commande `LAENGE`) :** cliquez sur la ligne près de l'extrémité à modifier. Ensuite, soit cliquez sur la nouvelle extrémité (elle est projetée sur la direction de la ligne, l'accrochage aux objets fonctionne), soit tapez la modification dans la ligne de commande : `+5` allonge de 5, `-5` raccourcit de 5, `=50` fixe la longueur à 50 (unité du projet). Cliquez ensuite sur la ligne suivante ou sur Échap.

**Aligner sur deux points (Édition > Aligner > Sur deux points, commande `ALIGN` / `AUSRICHTEN` / `AL`, comme dans AutoCAD) :** sélectionnez des objets (Entrée), puis le **1er point source** (un point de l'objet) → le **1er point de destination**, le **2e point source** → le **2e point de destination**. Avec une seule paire de points (Entrée au 2e point source), les objets sont simplement déplacés ; avec deux paires, ils sont aussi tournés autour du 1er point de destination pour que la ligne source 1-2 pointe vers destination 1-2. Enfin le programme demande « Mettre les objets à l'échelle d'après les points d'alignement ? » (par défaut **Non**) ; avec **Oui**, ils sont mis à l'échelle pour que les deux distances soient égales. Accrochage aux objets, ortho et coordonnées saisies fonctionnent comme pour Déplacer, un aperçu montre le résultat ; bloqué en 3D.

**Aligner les bords (Édition > Aligner, commandes `AUSLINKS`, `AUSRECHTS`, `AUSOBEN`, `AUSUNTEN`, `AUSMITTEH`, `AUSMITTEV`) :** sélectionnez au moins deux objets ; ils sont déplacés vers le bord gauche/droit/haut/bas ou vers le centre de la boîte englobante de toute la sélection.

**Manipulateur (Édition > sous-menu Manipulateur, barre d'outils, commande `MANIP`) :** active ou désactive une croix d'axes sur la sélection. Cliquez sur la **flèche X rouge** ou la **flèche Y verte** : l'objet ne se déplace que le long de cet axe. Quand vous cliquez le point cible, seule sa composante le long de l'axe compte — même si l'accrochage aux objets tombe sur un point à côté de l'axe, l'appareil reste sur sa ligne. Ou tapez la distance (`25`, `-10`). Le **carré jaune** déplace librement. Échap annule.

**Maquette filaire 3D (groupe de barres « 3D : » après Électricité, menu 3D, commande `3D`) :** le symbole 3D (cube) bascule la zone de dessin sur la vue 3D dans la même fenêtre — cliquez de nouveau pour revenir ; les outils 2D sont bloqués en 3D. Annuler/rétablir, calque, couleur, épaisseur de trait et toutes les autres fonctions de la fenêtre principale fonctionnent à l'identique. En 3D, le dessin 2D est couché à plat sur le plan de sol (z = 0) ; les volumes 3D sont affichés comme une simple maquette filaire (en 2D comme vue de dessus).
- **Vue :** bouton du milieu de la souris = orbite, **Ctrl + bouton du milieu** (ou glisser avec le bouton droit) = panoramique, molette = zoom, double-clic sur le bouton du milieu = « Tout afficher ». Le **cube de vue** (en haut à droite, affichable ou masquable) règle Dessus/Dessous/Avant/Arrière/Gauche/Droite en cliquant une face ; les quatre **flèches** autour du cube passent aux vues voisines ; glisser dans le cube fait tourner librement. Les icônes en haut de la zone 3D activent ou désactivent le cube de vue, la perspective et la **grille**, règlent la vue isométrique et affichent tout.
- **Calque, couleur, épaisseur en 3D :** la barre avec le calque, la couleur et l'épaisseur fonctionne ici aussi ; **double-cliquez** un objet pour ouvrir sa boîte de dialogue de dimensions (volumes/esquisses) ou ses propriétés ; **clic droit** (sans glisser) ouvre un menu : propriétés, modifier les dimensions, **copier**, **masquer le calque de cet objet**, afficher tous les calques, gérer les calques, supprimer. **Copier** (aussi pour les armoires et tous les autres volumes 3D) : la copie reste accrochée à la souris en aperçu jaune, l'accrochage aux objets attrape les coins des autres objets, un clic la dépose ; clic droit > Copier de nouveau pour d'autres copies, Échap annule, Ctrl+Z l'annule. **Vers une autre feuille :** sélectionnez les objets, Ctrl+C (ou Ctrl+X), changez de feuille, appuyez sur Ctrl+V dans la vue 3D — la copie reste accrochée à la souris, un clic la dépose. Cela permet de masquer des objets gênants sans repasser en 2D.
- **Dessiner sur les faces :** avec les **outils habituels** Ligne, Polyligne, Cercle, Rectangle et Cotation de la barre d'outils (dans la vue 3D, ils agissent automatiquement sur le plan de travail ou comme une cotation 3D — il n'y a pas d'icônes en double), passez simplement la souris sur un volume : la **face sous le curseur est surlignée en bleu** et le premier clic dessine directement sur cette face (plan de travail = cette face, en jaune avec grille et axes). Sans volume sous le curseur, c'est le plan de travail précédent ou le plan de sol qui s'applique. « Choisir une face » peut fixer une face au préalable ; « Plan de travail = plan de sol » coupe la détection automatique des faces. Le rayon, la largeur [×profondeur] ou la longueur peuvent être saisis dans le champ « Valeur » (Entrée ; fermer une polyligne par Entrée). L'esquisse peut ensuite être **extrudée vers le haut** (flèche Z ou « Extruder », bossage sur la face), entaillée dans le volume comme **alésage / poche** (icône « Perçage », profondeur 0 = traversant) ou tirée vers le bas (valeur négative = poche). Une ligne est ouverte et ne peut pas être extrudée.
- **Accrochage aux objets en 3D (OSNAP) :** lors du dessin sur les faces et de la cotation, un **marqueur visible** avec une étiquette montre le point d'accrochage sous le curseur : carré = extrémité (coins des volumes, extrémités de lignes et d'esquisses, points de quadrant des cercles), triangle = milieu (milieux d'arêtes), cercle avec croix = centre (cercles, fonds de cylindres/cônes/sphères), croix = point de grille. Les cotations s'accrochent à tous ces points dans l'espace ; le dessin s'accroche aux points qui se trouvent dans le plan de dessin.
- **Accrochage aux objets lors du placement et du déplacement (OSNAP, F3) :** lors du placement d'un volume ou d'un bloc (l'aperçu suit la souris), ses coins et milieux d'arêtes s'accrochent aux points d'accrochage des objets existants (carré jaune avec étiquette), de sorte que les armoires s'alignent ou s'empilent exactement. En faisant glisser une flèche du manipulateur (X/Y/Z), un coin de la sélection s'accroche à la coordonnée d'un point d'accrochage d'autres objets. Pour les blocs, ce sont les arêtes extérieures qui comptent (les pièces minces comme la porte, la poignée et la plaque de montage ne comptent pas). Sans OSNAP, seule la grille s'applique.
- **Sélecteur de couleurs avec RAL (partout où une couleur est choisie) :** boîte de dialogue propre au design de KatieCAD au lieu de la fenêtre système. À gauche la **palette RAL Classic** (filtre par groupe 1xxx jaune … 9xxx blanc/noir ; le survol affiche le numéro et le nom), à droite la saisie du **numéro RAL** (quatre chiffres, par ex. `5015` bleu ciel, `3020` rouge signalisation ; avec ou sans « RAL » ; pendant la saisie, la palette montre les couleurs correspondantes, Entrée applique sans fermer la boîte), de la **valeur hexadécimale** ou du **rouge/vert/bleu** ; pour les couleurs libres, le RAL le plus proche est affiché. Troisième onglet **« ACI (AutoCAD) »** avec l'AutoCAD Color Index 1-255 (saisir le **numéro ACI** à droite ou cliquer dans le tableau ; 1 rouge, 2 jaune, 3 vert, 4 cyan, 5 bleu, 6 magenta, 7 blanc/noir, 10-249 teintes, 250-255 gris) ; l'export DXF utilise la couleur ACI la plus proche. Deuxième onglet **« Champ de couleur »** : bande de teinte plus un carré saturation/valeur, avec des champs numériques **teinte 0-360** (par ex. 10 = rouge, 140 = vert, 240 = bleu), **saturation** et **valeur 0-100**. Les valeurs RAL sont des approximations à l'écran. « Sélecteur de couleurs du système ... » ouvre la boîte de dialogue du système d'exploitation si nécessaire.
- **Grille en 3D :** le même commutateur qu'en 2D s'applique (barre d'état « Grille », F7, icône dans la zone 3D). Le bouton « Pointillés » de la barre d'état affiche la grille — aussi sur le plan de sol et le plan de travail — en points au lieu de lignes.
- **Extruder comme AutoCAD :** dessinez un rectangle, un cercle ou une polyligne fermée en 2D, sélectionnez-le en 3D et faites glisser la **flèche Z bleue** vers le haut ou le bas (ou cliquez sur la flèche, tapez la hauteur dans le champ « Valeur », Entrée).
- **Sélection par fenêtre (comme en 2D) :** cliquez et faites glisser dans le vide. De **gauche à droite** (cyan), seuls les objets entièrement enfermés sont sélectionnés ; de **droite à gauche** (vert), tout ce que la fenêtre touche ; les objets touchés s'allument en magenta au préalable. Maj/Ctrl + fenêtre ajoute à la sélection, un simple clic dans le vide la vide. Orbite et panoramique restent sur le bouton du milieu ou Ctrl+bouton du milieu, et sur le bouton droit.
- **Étirer en 3D (Édition > Étirer, commande `STRETCH` / `ST`, comme en 2D) :** sélectionnez des objets 3D (aussi des armoires), lancez la commande, **cliquez le point de base du côté à déplacer** (par ex. sur l'arête supérieure ; coins, milieux et centres s'accrochent), puis **cliquez le point cible ou tapez la distance** (par ex. `200`, Entrée — il étire vers le côté où se trouve la souris par rapport au point de base ; `-200` inverse). L'axe est la direction principale du mouvement de la souris ; l'aperçu montre le résultat en jaune. Le côté du point de base se déplace de la distance : les grandes pièces (corps, porte, panneaux latéraux) s'allongent ou se raccourcissent, les petites pièces de ce côté (rails, accessoires) suivent, tout le reste reste en place. Les volumes sur des plans de travail, les sphères, les volumes fusionnés et les volumes avec découpes ne peuvent pas être étirés — ils restent inchangés (le message les compte). Ctrl+Z annule.
- **Rotation (icône « Rotation », menu 3D > Rotation autour d'un axe..., `3DDREHEN`) :** tourne la sélection autour de l'axe X, Y ou Z passant par l'origine du manipulateur (angle en degrés, positif = sens inverse des aiguilles d'une montre). Les volumes 3D, blocs, esquisses et cotations 3D tournent autour d'un axe quelconque, les formes 2D seulement autour de Z. Les alésages verticaux suivent le volume.
- **Arrondir les arêtes (icône « Arrondir les arêtes », `3DABRUNDEN`) :** boîte de dialogue avec un rayon et le choix des **arêtes supérieures** (bord de la face supérieure, « meulé par le haut »), **inférieures** et/ou **verticales** (coins vus de dessus). Fonctionne pour les pavés, prismes et cylindres (arêtes verticales seulement pour les volumes avec coins) ; les rayons trop grands sont limités. L'arrondi apparaît comme lignes de calque dans la maquette filaire.
- **Déplacer le manipulateur :** cliquez le petit **cercle orange** en diagonale sous le carré jaune (ou l'icône « Déplacer le manipulateur », `3DPIVOT`), puis cliquez un point (coins, milieux, centres s'accrochent) — le manipulateur s'y installe et sert de pivot pour la rotation. Il suit l'objet et revient au centre pour une nouvelle sélection (ou menu 3D > Centrer le manipulateur). **En 2D :** cliquez aussi le cercle orange (ou Édition > Déplacer le manipulateur), puis cliquez la nouvelle origine (l'accrochage aux objets fonctionne) ; « Centrer le manipulateur » restaure le milieu.
- **Découpes dans la vue 2D :** les découpes qui ne sont pas ouvertes vers le haut (faces latérales, dessous) apparaissent **en pointillés** (cachées) dans la vue en plan ; les perçages ouverts vers le haut restent pleins. Si plusieurs volumes ont des faces dans le même plan, l'alésage est entaillé dans le volume dont la face contient l'esquisse.

- **Manipulateur 3D :** les flèches X (rouge), Y (vert), Z (bleu) déplacent la sélection uniquement le long de cet axe ; avec l'accrochage, la distance s'aligne sur la grille. Avec l'icône « La flèche Z modifie la hauteur », la flèche Z modifie la hauteur d'un prisme/d'une pyramide au lieu de le déplacer. **Distance exacte :** pendant le glissement d'une flèche (bouton de la souris enfoncé), tapez simplement le nombre, par ex. `300` (Retour arrière efface, `-` pour le sens opposé) et validez par **Entrée** : le volume se déplace exactement de cette valeur (dans l'unité choisie) le long de l'axe ; la souris est ignorée pendant ce temps. Cela fonctionne aussi après un clic sur une flèche sans glisser : tapez le nombre, Entrée — ou écrivez le nombre dans la ligne de commande en bas ou dans le champ « Valeur ».
- **Volumes directs :** pavé, cylindre, cône, pyramide, sphère (icônes, menu 3D ou commandes `BOX`, `CYLINDER`, `CONE`, `PYRAMID`, `SPHERE`). Saisissez dimensions et position dans la boîte de dialogue ou choisissez la position sur le plan de sol (vue en perspective ou de dessus pour cela).
- **Armoire électrique (icône « Armoire », menu 3D, commande `CABINET`) :** bloc prêt à l'emploi de volumes simples. Dans la boîte de dialogue, choisissez une dimension courante dans la liste (11 tailles standard, de la version compacte à l'armoire au sol, données en largeur × hauteur × profondeur) ou « Dimensions libres » ; les valeurs restent modifiables. En option **avec/sans plaque de montage** (dimension adaptée à l'armoire ; librement réglable en dimensions libres), en option une **porte** (avec poignée rectangulaire et serrure, poignée à droite ou à gauche), un **panneau latéral gauche/droit** (tôles minces, légèrement en retrait pour être visibles dans la maquette filaire) et un **socle** (aucun, 100, 150 ou 200 mm) comme caisson sous l'armoire. La face avant regarde vers -Y, la plaque de montage se trouve à l'arrière. Le bloc peut être déplacé, tourné et dissous comme tout bloc 3D (pièces : socle, armoire, plaque de montage).
- **Modifier les dimensions après coup (`3DMASS`, double-clic) :** sélectionnez un volume ou une esquisse — modifiez largeur, profondeur, hauteur, rayon (formes libres : échelle en %).
- **Cotations 3D :** icône « Cotation 3D », cliquez deux points (les coins des volumes s'accrochent), puis la position de la ligne de cote. Fonctionne depuis n'importe quelle direction de vue sans repasser en 2D ; en 2D, elle apparaît en projection.
- **Texte en 3D :** l'outil « Texte » de la barre d'outils (automatiquement texte 3D en 3D) : passez la souris sur la face d'un volume (la face est surlignée, l'accrochage fonctionne), cliquez un point, saisissez texte, hauteur de texte et angle dans la face dans la boîte de dialogue (retour à la ligne avec ` | `). Le texte **repose sur la face ou le plan de travail choisi** (comme les lignes 3D) en texte à trait simple ; son coin inférieur gauche se trouve au point cliqué. Un **double-clic** le modifie ; déplacer/tourner/supprimer fonctionnent comme pour les autres objets. En 2D, il apparaît comme texte ordinaire sur les faces supérieures et comme lignes sur les faces verticales.
- **Distance en 3D (`MEASURE`, `DI`) :** dans la vue 3D, MEASURE donne la distance entre deux points de l'espace (accrochage aux coins/milieux/centres) et affiche la distance ainsi que dX, dY, dZ dans la barre d'état — sans créer de cotation. Mesurez d'autres paires de points ; Échap termine (les lignes de mesure disparaissent alors).
- **Propriétés (double-clic) :** ligne avec un champ **Longueur** (le modifier déplace l'extrémité, le point 1 reste) ; rectangle avec **Largeur/Hauteur** et redimensionnement depuis le coin 1 ou des deux côtés autour du centre.
- **Saisie pendant le dessin en 3D :** la **ligne de commande** en bas fonctionne comme en 2D : premier point en `x,y` sur le plan de travail, puis cercle = rayon, rectangle = `largeur,hauteur` (ou `largeur x hauteur`), ligne = longueur ou `longueur<angle`, polyligne = `x,y` ou `@dx,dy` (Entrée sur une ligne vide ferme). Sinon, le champ « Valeur » dans la zone 3D. **OSNAP (F3)** et **ORTHO (F8)** s'appliquent aussi en 3D : sans OSNAP, seule la grille s'accroche ; ORTHO limite lignes/polylignes à la direction X ou Y de la face et cotations/distances à un axe de l'espace.
- **Fonctions 2D en 3D :** Arc, Ellipse, Spline, Ajuster, Rupture, les outils électriques ainsi que Longueur, Congé/Chanfrein, Décalage et Aligner sont **grisés et bloqués** dans la vue 3D (message « 2D seulement ») — vous restez en 3D et pouvez les utiliser après être revenu en 2D.
- **3D dans une fenêtre de vue (présentation) :** cliquez une fenêtre de vue et appuyez sur l'icône 3D dans la présentation — la fenêtre de vue montre le modèle en maquette filaire isométrique (la présentation reste, la fenêtre 3D ne la remplace plus). Activez la fenêtre de vue par un double-clic (un double-clic dans une autre fenêtre de vue bascule directement dessus, un double-clic à l'extérieur quitte la vue de la fenêtre — chaque fenêtre de vue peut donc montrer sa propre vue), puis **glissez avec le bouton du milieu = rotation**, bouton droit = panoramique, molette = zoom. Clic droit > « Vue 3D dans cette fenêtre de vue » propose des vues standard (isométrique, dessus, avant ...) ou reprend la caméra de la vue 3D. La fenêtre de vue est imprimée à l'échelle et exportée en PDF. Appuyer de nouveau sur l'icône 3D ou sur « Retour à la vue 2D » restaure l'état normal.
- **Bloc 3D :** sélectionnez plusieurs volumes 3D › icône « Créer un bloc 3D » (`3DBLOCK`) ; le bloc est sélectionné et déplacé comme une seule unité. Il ne sert qu'à la vue d'ensemble et n'a aucune fonction électrique. « Dissoudre le bloc 3D » le sépare de nouveau.
- **Fusionner des volumes 3D (menu 3D, commande `3DVERSCHMELZEN` / `3DUNION`, clic droit > « Fusionner les volumes ») :** sélectionnez au moins deux volumes 3D (aussi des blocs 3D entiers comme des armoires). Ils sont réunis en **un** seul volume (union booléenne) : les recouvrements et arêtes intérieurs disparaissent, seule la peau extérieure commune demeure ; les trous et découpes des pièces sont conservés. Le nouveau volume peut être déplacé, tourné, mis à l'échelle, copié et supprimé comme tout autre, il est enregistré avec le projet et fonctionne avec « Masquer les arêtes cachées » et dans le PDF. **Limites :** les pièces ne peuvent plus être modifiées individuellement (tirer la hauteur, perçages et arrondis ne sont pas possibles sur le volume fusionné, dimensions seulement par facteur ; Ctrl+Z restaure les volumes individuels). Les volumes ronds sont fusionnés comme des polygones (les transitions lisses ne sont pas dessinées comme arêtes, les lignes des volumes d'origine sont conservées). Les volumes qui ne se touchent pas sont tout de même réunis en un objet (avec des parties séparées). Une armoire devient une simple enveloppe extérieure — la plaque de montage intérieure disparaît.
- **Masquer les arêtes cachées :** le bouton *Masquer les arêtes cachées* de la barre 3D (cube avec arêtes arrière en pointillés) montre les volumes comme un modèle solide : les arêtes couvertes par un volume devant disparaissent (il n'y a volontairement pas d'arêtes arrière en pointillés), et une armoire n'a plus qu'une seule lecture possible. Une **armoire sans porte est ouverte à l'avant**, même sans plaque de montage : l'intérieur (et la plaque de montage, s'il y en a une) reste visible, aussi quand l'armoire est tournée. Pendant la rotation, le panoramique et le zoom, KatieCAD affiche la maquette filaire complète pour la vitesse et recalcule ensuite. Les volumes sélectionnés ne sont surlignés que le long de leurs arêtes visibles.
- **Arêtes cachées dans la présentation et dans le PDF :** dans la présentation, le même réglage existe par fenêtre de vue : clic droit sur la fenêtre de vue > *Vue 3D dans cette fenêtre de vue* > *Masquer les arêtes cachées* (coché = activé). Il est enregistré avec le projet, reste lorsque la vue standard change et s'applique aussi à la sortie PDF. « Reprendre la caméra de la vue 3D » reprend aussi l'état du bouton 3D. Une armoire peut ainsi être mise en place une fois en 3D, masquée et imprimée proprement.
- **Masquer les portes d'armoire par fenêtre de vue (depuis 1.1.3) :** clic droit sur la fenêtre de vue > *Vue 3D dans cette fenêtre de vue* > *Masquer les portes d'armoire* (coché = activé). Porte, poignée et serrure de toutes les armoires disparaissent dans cette fenêtre de vue seulement ; le modèle lui-même reste inchangé. Une armoire avec plaque de montage peut ainsi apparaître dans la même présentation une fois avec et une fois sans porte, sans la dessiner deux fois (fenêtre de vue 1 : avant avec porte, fenêtre de vue 2 : ouverte avec plaque de montage, fenêtre de vue 3 : côté). Une armoire sans porte est ouverte à l'avant (voir arêtes cachées). Le réglage est enregistré, s'applique à l'accrochage aux objets, à la cotation et à la sortie PDF, et reste lorsque la vue standard change.
- **Cube de vue et bouton « Caché » dans la présentation :** une fenêtre de vue 3D **sélectionnée ou active** (activer « Vue 3D » la sélectionne automatiquement) montre le cube de vue avec les flèches de rotation en haut à droite : un clic sur une face du cube règle la vue standard (Dessus, Avant, Gauche ...), les flèches tournent par pas de 90°/45°, glisser le cube fait tourner librement. En dessous, le bouton **Caché** (coché = activé) bascule les arêtes cachées de cette fenêtre de vue — le même réglage que dans le menu du clic droit. Le cube n'apparaît qu'à l'écran, jamais à l'impression ni dans le PDF, et seulement dans les fenêtres de vue assez grandes. Chaque modification peut être annulée par Ctrl+Z.
- **Déplacer et copier de point en point en 3D :** sélectionnez le ou les objets, puis cliquez sur *Déplacer de point en point* dans la barre 3D (ou Édition > Déplacer (point de base), ou commande `V`/`M`, copie avec `CO` — dans la fenêtre 3D, elles agissent maintenant dans l'espace). Cliquez d'abord le **point de base**, par ex. un coin de l'armoire, puis le **point cible**, par ex. le coin d'un autre objet. Avec l'accrochage aux objets activé (F3), les deux points s'accrochent aux **coins, milieux d'arêtes et centres** (marqueur jaune avec étiquette) ; ORTHO (F8) limite le déplacement à un axe. Pendant le pointage, un aperçu en pointillés montre la sélection déplacée avec la distance. Échap annule, Ctrl+Z annule. Les deux fonctions sont aussi dans le **menu du clic droit** (*Déplacer avec point de base*, *Copier avec point de base*). Faire glisser les axes du manipulateur continue de s'accrocher axe par axe. **Limites :** les points d'accrochage sont les coins, milieux et centres ; les intersections d'arêtes existent rarement dans l'espace (deux lignes ne se rencontrent presque jamais exactement) et ne sont pas accrochées.
- **Accrochage aux objets dans la présentation sur le contenu des fenêtres de vue :** dans la présentation, l'outil ligne, cotation, texte et tous les autres outils s'accrochent désormais aussi aux points **à l'intérieur des fenêtres de vue**, sans devoir activer la fenêtre de vue. Dans les **fenêtres de vue 2D**, tous les types d'accrochage du modèle s'appliquent (extrémité, milieu, centre, quadrant, intersection ...) ; dans les **fenêtres de vue 3D**, les **coins, milieux d'arêtes et centres** des volumes dans la vue affichée (avec arêtes cachées activées, seulement les points sur les arêtes visibles). Les objets de la présentation elle-même sont prioritaires. Les types d'accrochage peuvent être désactivés individuellement comme d'habitude (F3 les désactive tous). Une **cotation dans la présentation** dont les points se trouvent dans une fenêtre de vue affiche désormais la **valeur du modèle** (distance papier divisée par l'échelle de la fenêtre de vue) et non plus des millimètres papier ; une armoire construite en 3D peut donc être cotée à l'échelle dans la présentation. Si les points sont en dehors d'une fenêtre de vue, la mesure papier reste ; le « texte de remplacement » modifie la valeur à tout moment. Les cotations angulaires ne sont pas concernées.
- **Masquer les champs des bornes :** dans la boîte de dialogue des bornes (placement et double-clic), chaque champ (IND, MAN, TYP, PER, NUM) a la case à cocher *afficher*, comme pour les appareils. Les champs masqués n'apparaissent pas dans le dessin mais restent disponibles pour le plan de borniers, la liste des appareils et la nomenclature ; les lignes visibles remontent. Il en va de même pour le masque d'appareil. Le choix est conservé tant que vous placez plusieurs bornes à la suite.
- **Taille de la fenêtre :** la fenêtre principale a une taille minimale (1010 × 600 pixels, la taille de l'écran sur les écrans plus petits) pour que les barres d'outils, la barre d'état et la ligne de commande restent toujours utilisables.
- **Mesures réelles dans une fenêtre de vue :** une cotation dans la présentation mesure la **projection** des points sur le papier. Elle n'affiche la longueur réelle que si la vue est alignée exactement sur un axe (Avant, Arrière, Gauche, Droite, Dessus, Dessous) et non en perspective. Quelques degrés d'inclinaison faussent déjà la mesure (par ex. socle de 150 mm → 149,70 mm, et des points à des profondeurs différentes, comme l'arête avant et l'arête arrière, se décalent l'un par rapport à l'autre). C'est pourquoi, en tournant une fenêtre de vue (bouton du milieu ou cube de vue), la vue **s'aligne exactement sur une direction standard à moins de 4 degrés**. Pour une vue déjà inclinée : clic droit > *Vue 3D dans cette fenêtre de vue* > *Avant* (etc.).
- **Clic droit dans la présentation au-dessus d'une fenêtre de vue :** si un objet se trouve sous le pointeur (cotation, texte, ligne ...), son menu s'ouvre avec *Déplacer (point de base)*, *Copier (point de base, multiple)* et *Copier avec point de base* ; le menu de la fenêtre de vue n'apparaît que sur la fenêtre de vue libre. Le menu de la fenêtre de vue a désormais les trois mêmes entrées pour le cadre de la fenêtre de vue.
- **Texte de cotation et autres propriétés de la cotation :** un double-clic sur une cotation (ou clic droit > Propriétés, Ctrl+1) ouvre les propriétés de la cotation — y compris le champ *Texte affiché* avec la valeur mesurée à côté. Il peut contenir n'importe quel texte, par ex. **150**, même si la mesure est autre ; `<>` représente la valeur mesurée (« <> mm », « env. <> ») ; *Rétablir la valeur mesurée* (ou un champ vide) affiche de nouveau la valeur mesurée. La commande `MASSTEXT` ouvre les mêmes propriétés. Le texte est enregistré avec le dessin, apparaît dans le PDF et Ctrl+Z l'annule. **Hauteur de texte, police, taille de flèche et extrémité** (*Flèche* ou *Trait oblique* — le trait oblique de la cotation architecturale ; pour les nouvelles cotations aussi dans la barre d'outils) s'y règlent également ; dans la fenêtre des propriétés (Ctrl+1), cela fonctionne aussi pour plusieurs cotations à la fois (l'angle du texte reste verrouillé pour les cotations, il suit la direction de mesure). Les **décimales** (0 à 6, par ex. 800 ou 800.0000) se règlent là aussi ou par clic droit > *Décimales* ; les nouvelles cotations utilisent la valeur de la barre d'outils.
- Tout le reste reste une simple maquette filaire (ni faces, ni rendu).

**Placer les barres d'outils (Affichage > Barres d'outils, ou faire glisser la poignée ⋮⋮) :** il y a une barre chacune pour les **Outils**, l'**Électricité** et la **3D**. Le bouton ☰ qui affiche ou masque le panneau latéral a une place fixe en **bas à gauche** de la barre d'état (aussi F4) et reste visible tant que le panneau latéral est masqué. Chacune peut être ancrée séparément en haut, en bas ou à droite — faites glisser la poignée au début de la barre vers le bord de fenêtre souhaité et relâchez, elle s'y accroche. En haut ou en bas, les barres se placent côte à côte et passent sur une nouvelle ligne dans une fenêtre étroite ; à droite, les symboles se répartissent en plusieurs colonnes. L'**ordre** se modifie via Affichage > Barres d'outils > « Avancer / Reculer » ou en déposant la poignée sur une autre barre (par ex. Électricité avant Outils). Le choix est enregistré par barre.

**Sélection rapide (Édition > Sélection rapide, commande `QS`) :** sélectionne tous les objets d'un type d'objet, calque, couleur ou type de ligne. Plusieurs critères s'appliquent ensemble (ET). En option, sélectionner tout sauf les correspondances ou ajouter à la sélection courante.

**Cotation chaînée (Insertion > Cotation > Cotation chaînée, commande `KETTE`) :** deux points de mesure et la position de la ligne de cote comme pour la cotation normale ; ensuite un clic par point supplémentaire suffit, et chaque nouvelle cotation part du dernier point sur la même ligne de cote. Échap ou clic droit termine.

**Mesurer (Édition > Mesurer, commandes `MEASURE` / `DI`) :** cliquez deux points (l'accrochage aux objets fonctionne). KatieCAD affiche distance, dX, dY et angle dans la barre d'état et dessine le segment mesuré. D'autres clics démarrent une nouvelle mesure, Échap ou clic droit termine. Les valeurs utilisent l'unité courante.

**Congé et chanfrein (Édition > Congé / Chanfrein, commandes `FILLET` ou `F`, `CHAMFER`) :** saisissez le rayon ou les distances de chanfrein, puis cliquez deux lignes l'une après l'autre. Les lignes sont ajustées (ou prolongées) au coin et reliées par un arc ou une ligne de chanfrein ; le côté le plus long de chaque ligne est conservé. Rayon 0 / distance 0 ferme simplement le coin. Vous pouvez aussi cliquer un **rectangle ou une polyligne** : un clic sur un coin arrondit seulement ce coin, un clic sur une arête arrondit tous les coins ; l'objet est décomposé en lignes et vrais arcs. Des lignes parallèles ou un rayon trop grand donnent « impossible ». La boîte de dialogue mémorise les dernières valeurs ; Échap termine.

**Ellipse et spline (Insertion > Ellipse / Spline, commandes `ELLIPSE`, `SPLINE`) :** *Ellipse :* centre, fin du premier axe, puis la longueur du second demi-axe (clic ou coordonnées dans la ligne de commande). Les poignées modifient le centre et les deux demi-axes ; rotation, échelle et symétrie fonctionnent aussi. *Spline :* placez les points de passage l'un après l'autre, la courbe passe de façon lisse par tous ; Entrée ou clic droit termine, un clic sur le point de départ ferme la courbe. Chaque point de passage a une poignée. L'export DXF écrit les deux comme polylignes (les ellipses et splines DXF importées restent des polylignes). À l'intérieur de blocs ou après décomposition, elles deviennent de simples polylignes.

**Locaux (Insertion > Local, bouton « Local », commande `ROOM` ; depuis 1.1.3) :** cliquez les **coins du local** l'un après l'autre (nombre quelconque, aussi en L ou en U, avec accrochage aux objets sur les coins de mur intérieurs si vous voulez) ; un clic sur le premier point (ou Entrée / clic droit) ferme le local. Saisissez ensuite le numéro et le nom du local. En dessous apparaît la **surface en m²**, calculée automatiquement (unité du dessin : mm). Le cadre est **invisible** — seul le texte est affiché. Un clic sur le texte sélectionne le local et montre le cadre avec des **poignées de coin** : servez-vous-en pour modifier la taille du local (la surface est recalculée) ; la poignée du centre ne déplace que le texte. Un double-clic sur le texte (ou clic droit > *Modifier le local*) modifie numéro, nom, **police** (aussi gras) et hauteur de texte. Les locaux sont sur le calque « Räume » (peut être masqué) ; le PDF et le DXF ne contiennent que le texte.

**Murs, portes et fenêtres (Insertion > Mur / Porte dans le mur / Fenêtre dans le mur, commandes `WALL`, `DOOR`, `WINDOW` ; depuis 1.1.3) :** pour les plans de bâtiment, en 2D seulement. *Mur :* l'outil demande d'abord l'**épaisseur du mur** (mm) et la **position de la ligne dessinée** (axe du mur, face gauche ou droite). Cliquez ensuite les points d'angle l'un après l'autre (ou tapez coordonnées ou longueur et angle dans la ligne de commande) ; Entrée ou clic droit termine, un clic sur le point de départ (ou `S`) ferme un local. Le mur apparaît avec ses deux faces et des coins en onglet sur son **propre calque « Wände »**, créé automatiquement. Il peut être déplacé, tourné, mis à l'échelle, symétrisé et copié comme tout objet, dispose de l'accrochage aux objets sur toutes les arêtes et coins (pour la cotation) et se sélectionne en cliquant le corps du mur ; un **double-clic** modifie l'épaisseur, la position de la ligne et les **hachures** (aucune, diagonale 45°, croisée ou **remplissage plein** ; espacement des lignes réglable, 180 mm par défaut) — les hachures remplissent uniquement le corps du mur, laissent libres les ouvertures de portes et fenêtres et ne nécessitent aucune commande de hachures ; un clic droit > *Hachurer le mur (on/off)* ou la commande `WALLHATCH` le fait en un clic. **Assembler des murs :** le bouton *Assembler des murs* de la barre d'outils (ou *Insertion > Assembler des murs*), puis cliquez les deux murs l'un après l'autre — ils sont fusionnés aussitôt. Sinon, sélectionnez deux murs et utilisez le clic droit > *Assembler des murs* ou la commande `WALLJOIN`. Les deux murs sont réunis à leurs extrémités les plus proches en **un** mur avec un coin en onglet propre : les lignes d'axe sont prolongées ou ajustées à leur intersection commune, aussi pour deux extrémités opposées en ligne (un petit écart est comblé). Portes et fenêtres gardent leur aspect. Impossible : murs fermés (locaux), murs parallèles éloignés et extrémités trop éloignées du point de coin (un message apparaît) ; **Fermer un mur :** cliquez le même mur une seconde fois (ou sélectionnez un mur > clic droit > *Fermer le mur*) : début et fin sont réunis en un coin en onglet propre et le mur est fermé. **Jonction en T :** si l'extrémité d'un mur se trouve devant ou au milieu de l'autre, elle est prolongée ou ajustée sur sa ligne d'axe (les deux murs restent). **Les murs qui se touchent ou se recouvrent forment automatiquement un contour commun :** les faces de mur et les hachures à l'intérieur d'un autre mur ne sont pas dessinées. Avec **Ortho (F8)**, les points de mur peuvent aussi être tirés par leurs poignées horizontalement ou verticalement par rapport au point voisin. (Le bouton « Modifier la longueur » à côté est un outil séparé, plus ancien, sans lien avec les murs.) *Modèles de porte :* choisir d'abord « Porte » ou « Fenêtre » affiche la **fenêtre des propriétés** (les valeurs s'appliquent à tous les clics suivants) ; pour les portes, choisissez le **modèle** : *Un vantail*, *Porte à deux vantaux* (deux vantaux égaux), *Porte à deux vantaux avec un grand vantail* (part en % réglable ; la case « Grand vantail de l'autre côté » échange le côté) ou *Rideau métallique* (ligne en pointillés dans l'ouverture du mur, sans vantail). Des tailles usuelles sont proposées quand le modèle change. *Portes et fenêtres* sont des **objets à part entière, tout à fait normaux :** choisissez l'outil et cliquez sur le mur — l'objet s'y installe et suit la direction et l'épaisseur du mur ; une porte découpe automatiquement l'ouverture dans le mur. Ensuite, ils peuvent être **sélectionnés, déplacés (poignée du centre ou Déplacer avec point de base), copiés, symétrisés, tournés et supprimés comme tout objet** ; les deux poignées d'extrémité modifient la largeur. Un **double-clic sur une porte ou une fenêtre** ouvre ses propres propriétés : largeur, hauteur (fenêtres aussi allège) et, pour les portes, les cases *Charnière de l'autre côté* et *La porte s'ouvre de l'autre côté du mur*. Les deux mêmes commutateurs sont dans le menu du clic droit. Un mur peut avoir un nombre quelconque de portes et de fenêtres. Le DXF et le PDF produisent tout en lignes ; enregistrés comme bloc, mur, portes et fenêtres deviennent de simples lignes. Dans la vue 3D, les outils de mur sont bloqués (comme les autres outils 2D).

**Chemins de câbles (Insertion > Chemin de câbles / Assembler des chemins de câbles, commandes `DUCT`, `DUCTJOIN` ; depuis 1.1.6) :** les outils sont dans la nouvelle barre **« Bâtiment : »** (avec Mur, Porte, Fenêtre, Assembler des murs et Local ; la barre peut être déplacée comme les autres, Affichage > Barres d'outils). Les chemins de câbles sont sur leur propre calque **« CD »** (rouge), créé automatiquement. *Chemin de câbles :* l'outil demande la **largeur** (en 3D aussi la **hauteur**) et la **position de la ligne dessinée** (axe du chemin, bord gauche ou droit, comme pour les murs) ; cliquez ensuite les points l'un après l'autre — chaque tronçon entre deux clics est un chemin droit séparé (Entrée ou clic droit termine ; coordonnées, longueur et angle peuvent être saisis comme pour le mur). **En 2D**, un chemin plat est dessiné dans la zone du modèle ; **dans la vue 3D**, un volume avec largeur et hauteur est créé automatiquement sur la face sous la souris (ou sur le plan de travail). **Hachures :** comme pour les murs (aucune, diagonale 45°, croisée ou remplissage plein, espacement réglable, 20 mm par défaut) — dans la boîte de dialogue avant le dessin ou après par **double-clic** (largeur et hauteur aussi là ; pour les pièces de raccordement, seulement les hachures) ; 2D seulement. **Ouverture dans le mur** (Insertion > Ouverture dans le mur, commande `OPENING`, dans la barre « Bâtiment : ») : comme une fenêtre, mais sans vitrage — cliquez le mur, le mur reçoit une ouverture avec tableaux ; largeur, hauteur et allège par double-clic. *Assembler des chemins :* cliquez les deux chemins l'un après l'autre — la pièce de raccordement correspondante est créée comme **composant à part** : **manchon** (extrémités en ligne), **coude** (angle) ou **té** (un chemin se termine sur le côté de l'autre) ; les dimensions (largeur, hauteur) découlent des chemins. En 3D, les deux chemins doivent se trouver dans le même plan. Les pièces de raccordement n'ont pas de dimensions propres ; supprimez-les et recréez-les. Les chemins peuvent être déplacés, tournés, copiés et supprimés comme tout objet ; le DXF et le PDF les produisent comme lignes.

**Annuler un mur ou un local (depuis 1.1.4) :** **Échap** écarte le mur ou le local en cours et garde l'outil actif ; un second Échap revient à la sélection.

**Cotation angulaire (Insertion > Cotation > Cotation angulaire (3 points) / (2 lignes), commandes `ANGULAR`, `WINKELLINIEN`) :** *3 points :* sommet, point sur le premier côté, point sur le second côté, puis cliquez la position de l'arc de cote. *2 lignes :* cliquez les deux lignes (le sommet est leur intersection, le côté cliqué choisit le côté), puis placez l'arc. Le secteur angulaire est celui qui contient l'arc de cote, de sorte que les angles supérieurs à 180° peuvent aussi être cotés. Poignées pour le sommet, les deux côtés, l'arc et le texte ; hauteur de texte, flèche et décimales fonctionnent comme pour les autres cotations.

**Purger les calques :** dans la fenêtre des calques (« Calques... »), **Purger** supprime tous les calques qu'aucun objet n'utilise — dans un projet, sur toutes les feuilles (aussi présentations et blocs). Le calque 0 et le calque actif restent. KatieCAD demande d'abord avec la liste. Ctrl+Z n'annule que sur la feuille ouverte ; les autres feuilles sont enregistrées immédiatement.

**Importer des calques et un modèle :** les couleurs de calque appartiennent au dessin — un bloc ne transporte que le nom du calque. Pour ne pas devoir tout configurer dans chaque nouveau dessin, la fenêtre des calques a trois boutons : **Importer depuis un fichier...** copie les calques (avec couleur et épaisseur) d'un autre dessin ou projet dans le courant ; les calques existants restent, si la couleur ou l'épaisseur diffère, on vous demande une fois s'il faut écraser. **Enregistrer comme modèle** mémorise tous les calques du dessin courant pour les **nouveaux** dessins (Fichier > Nouveau, nouveau projet) ; les fichiers ouverts ou existants ne sont jamais modifiés. **Réinitialiser le modèle** rétablit les calques par défaut. Les calques manquants dont un bloc a besoin sont créés automatiquement lors de son insertion (couleur du modèle ou du bloc).

**Hachures comme AutoCAD :** sans rien de sélectionné, choisissez Insertion > Hachures, réglez motif, espacement et angle, puis cliquez directement dans une zone fermée. KatieCAD trouve la plus petite région autour du point cliqué (les lignes peuvent se croiser ; cercles, rectangles et polylignes comptent aussi) et la hachure. Cliquez plusieurs zones l'une après l'autre ; Échap ou clic droit termine. Si une limite fermée est déjà sélectionnée, c'est elle qui est hachurée comme avant.

**Étirer avec une présélection :** si vous avez sélectionné des objets au préalable avec une fenêtre de capture (de droite à gauche), **Étirer** (`STR`) saute directement au point de base — pas besoin d'une seconde fenêtre. Seuls les objets sélectionnés sont étirés. Avec un autre type de présélection (par ex. clic simple), la sélection est conservée et vous ne faites que tirer la fenêtre.

**Étirer des murs :** les murs s'étirent comme des polylignes : tirez une fenêtre de capture autour de l'extrémité du mur (et des portes et fenêtres qui lui appartiennent) — les points d'angle à l'intérieur de la fenêtre bougent, les portes et fenêtres dont le centre est dans la fenêtre suivent. Les murs qui touchent seulement un autre mur (jonction en T) ne suivent pas automatiquement : la fenêtre doit aussi attraper le mur voisin, sinon un vide apparaît.

## 5. Projets et feuilles

Un **projet** est un dossier avec un fichier de projet (`*.katieprj`), un fichier par feuille
(`Blatt_001.cadjson` …) et un dossier `Bloecke` pour les fichiers de blocs.

Menu **Projet** :

- **Créer un projet…** : choisissez un nom et un emplacement. La première feuille est créée.
- **Ouvrir / enregistrer / fermer / renommer… / supprimer un projet…**
- **Nouvelle feuille, dupliquer la feuille, propriétés de la feuille (F2 : nom et emplacement de montage), supprimer la feuille**
- **Imprimer le projet…**
- **Créer / mettre à jour la documentation…** et **Exporter les listes en CSV…** (voir section 9)

Dans le **panneau latéral**, un clic change de feuille. La feuille courante est enregistrée
automatiquement. Un double-clic renomme une feuille. Sélectionnez plusieurs feuilles avec **Ctrl** ou **Maj** + clic
pour les déplacer ensemble avec les boutons fléchés ou les supprimer avec « − » (tant que plusieurs
feuilles sont sélectionnées, la feuille courante reste ouverte). L'annulation est conservée par feuille.

Sans projet, vous travaillez sur un seul dessin (menu **Fichier** : Nouveau, Ouvrir, Enregistrer …).

## 6. Modèle, présentation, cadre, impression

- **Modèle** (menu **Affichage**) : le dessin proprement dit, en taille réelle (mm).
- **Présentation** : la feuille de papier (par ex. DIN A4 paysage). Elle porte le cadre, le cartouche
  et des **fenêtres de vue**, qui sont des fenêtres sur le modèle avec leur propre échelle.
  Créez une fenêtre de vue avec **Insertion > Placer une fenêtre de vue**.
- **Insertion > Cadre + cartouche…** : place le bord de feuille et un cartouche d'après un
  modèle. Vos propres cartouches sont des dessins ordinaires (`*.cadjson`) dans le dossier
  `title_blocks/` ; leur origine est le coin inférieur droit du cadre de la feuille.
  Des champs comme `PAGE`, `PAGES`, `SHEET`, `PROJECT`, `DATE`, `SCALE`, `FORMAT` sont
  remplis automatiquement. Avec **Projet > Propriétés du projet…**, vous saisissez le client,
  dessiné par / vérifié par, le numéro de dessin et le tableau des révisions (4 lignes : indice, modification,
  nom, date) une fois ; ils apparaissent dans les cartouches de toutes les feuilles. Le titre est composé du
  client, du nom du projet et du nom de la feuille ; le format papier suit le format de la présentation.
  Les noms de champs (par ex. `CUSTOMER`, `DRAWN`, `REV1_INDEX`) sont listés dans
  `title_blocks/README.md`.
- **Insertion > Enregistrer le dessin comme modèle de cartouche…** transforme un dessin en nouveau
  modèle.
- **Fichier > Imprimer** (Ctrl+P) et **Projet > Imprimer le projet…** créent un PDF
  (plusieurs feuilles dans un fichier) ou ouvrent l'aperçu avant impression.

## 7. Blocs et attributs

Un **bloc** est un groupe d'objets réutilisable (par exemple un symbole). Menu **Blocs** :

- **Créer un bloc (B)** : sélectionnez des objets, appuyez sur `B`, cliquez le point de base, choisissez un
  nom et un emplacement d'enregistrement.
- **Insérer un bloc/appareil (I)** ouvre le navigateur de blocs. Un double-clic sur un bloc le place
  dans le dessin. Les blocs sont des fichiers ordinaires (`*.katieblock`) dans les dossiers affichés par
  le navigateur (dont le dossier de projet `Bloecke`).
- **Décomposer le bloc (X)** sépare de nouveau un bloc ; les attributs restent des attributs (la valeur courante
  devient la valeur par défaut). Pendant le glissement d'une poignée d'extrémité de ligne, l'accrochage aux objets et Ortho fonctionnent.
- **Enregistrer un bloc/appareil dans un fichier / charger un bloc depuis un fichier** (une entrée commune dans le menu Blocs ; l'entrée en double dans le
  menu Électricité a disparu).
- **Définir un attribut (ATTDEF)** : un champ de texte à l'intérieur du symbole dont la valeur diffère
  par bloc inséré. Sélectionnez-le avec la géométrie du symbole et créez le
  bloc. KatieCAD demande les valeurs lors de l'insertion. **Modifier les attributs (ATTEDIT)**
  les modifie plus tard. Pour les appareils à très nombreuses broches (par ex. modules API à 16 voies), la liste de la fenêtre est
  **défilante** (molette ou barre à droite) ; OK et Annuler restent toujours visibles.
- **Textes lisibles lors de la rotation :** les textes et attributs d'un bloc ne sont jamais à l'envers. Si le bloc est tourné (par ex. de 180 degrés)
  de sorte qu'un texte serait inversé, KatieCAD retourne le texte de 180 degrés et symétrise son point d'ancrage — il reste
  lisible et du même côté du symbole. Les textes verticaux (90 / 270 degrés) restent possibles. Aucun réglage nécessaire ;
  les symboles de plans de bâtiment peuvent être tournés librement sans que les textes de fonction (par ex. le « E » dans le carré)
  deviennent illisibles.
- **Variantes (comme EPLAN) :** un bloc / appareil peut avoir plusieurs variantes — par ex. une prise en quatre
  orientations, avec des textes de fonction bien placés. **Créer :** créez le bloc avec la première variante. Sélectionnez
  un autre dessin (même référence de point de base, avec des textes d'attribut comme `IND`) > *Blocs > Ajouter une variante au bloc...* >
  cliquez le point de base > choisissez le **fichier de bloc** (`.katieblock`) auquel la variante appartient > saisissez le nom de la
  variante (suggestion A, B, C ...). Le même nom remplace la variante. KatieCAD l'ajoute au fichier lui-même — toutes les variantes sont
  alors réunies dans ce seul fichier. **Choisir :** lors de l'insertion et plus tard par double-clic ou *Modifier les attributs*, le champ
  **Variante** est en haut. Les valeurs d'attribut, les réglages d'appareil et les liens sont conservés lors du changement ; les positions de texte
  librement déplacées de l'ancienne variante sont réinitialisées. Une rotation supplémentaire reste possible (textes jamais à l'envers).
  Les appareils déjà placés reprennent les variantes ajoutées plus tard dès que vous ouvrez leur boîte de dialogue (double-clic),
  à condition que le bloc soit chargé dans la bibliothèque (par ex. après l'ajout de la variante ou une nouvelle insertion depuis le navigateur de blocs).

### Références externes (XREF ; depuis 1.1.7)

Une **référence** place un autre dessin sous le dessin courant (par ex. un plan d'étage sous un plan
d'installation) sans le copier. Menu **Blocs > Références externes (XREF)...** ou la commande `XREF` ouvre
la fenêtre avec toutes les références du dessin.

- **Ajouter...** (ou `XATTACH`) : choisissez un fichier (`*.cadjson`, aussi `*.dxf` et `*.dwg`) et cliquez ou tapez
  le point d'insertion, comme pour un bloc. Tournez, mettez à l'échelle et déplacez l'objet pour ajuster position et
  échelle.
- **On / Off** (ou double-clic sur la ligne) : active ou désactive la référence. Off = non dessinée et non
  accrochable.
- **Mettre à jour** relit le fichier. Si le fichier source change, la référence se met à jour d'elle-même
  aussi.
- **Changer le chemin...** pointe vers un autre fichier (par ex. après l'avoir déplacé). **Supprimer** supprime la
  référence.
- La référence est **en affichage seul et ne peut pas être modifiée**, mais l'accrochage aux objets fonctionne dessus. Elle ne peut
  pas être décomposée. Les calques masqués du fichier source ne sont pas repris. Murs, portes, fenêtres, locaux et cotations
  apparaissent comme dans la source.
- Seul le chemin est enregistré (relatif au dossier du projet ou au fichier quand c'est possible, sinon absolu). Si
  le fichier manque, la fenêtre affiche « Fichier manquant » et vous pouvez changer le chemin. Un dessin
  ne peut pas se référencer lui-même ; les références à l'intérieur de références sont lues jusqu'à
  cinq niveaux.
- Les références existent dans la zone du modèle ; dans une présentation, elles apparaissent dans les fenêtres de vue.
  Elles ne participent pas à l'évaluation électrique (liste des appareils, renvois) et apparaissent dans le DXF/DWG
  et le PDF comme géométrie simple.

## 8. Électricité : dessiner un schéma

Tous les outils sont dans le menu **Électricité** et dans la barre d'outils.

**Calques automatiques :** les objets électriques ne vont plus sur le calque 0 mais sur des calques que KatieCAD crée à la demande : **E_DEVICES** (appareils), **E_LINES** (fils, jonctions, renvois), **E_CABLE** (définitions de câbles), **E_CLAMPS** (bornes) et **E_PIN** (broches isolées tant qu'elles ne sont pas réunies en appareil ; à l'intérieur d'un appareil, elles appartiennent à E_DEVICES). Les objets existants restent inchangés ; les calques peuvent être masqués ou recolorés comme tout autre.

### Éléments de construction

| Élément | Rôle |
|---|---|
| **Broche** (PIN) | Point de connexion avec une étiquette (par ex. `1`, `2`, `A1`). Les fils s'y terminent. |
| **Masque électrique** (MASKE) | Champ d'étiquette d'un appareil : **IND** (repère, par ex. `K1`), **TYP** (type), **PER** (désignation). **REF** se remplit seul. |
| **Jonction** (VERBINDUNG) | Coin, dérivation en T ou croisement. Dans la boîte de dialogue, cochez les directions (Nord/Ouest/Est/Sud) qui reçoivent une liaison par fil (au moins 2) et éventuellement « Avec point » (= relié électriquement). Le point fonctionne aussi pour une dérivation en T à 3 directions ; un croisement à 4 directions sans point n'est qu'un croisement de fils. |
| **Renvoi** (QV) | Flèche qui continue un circuit sur une autre feuille. Même texte = même circuit. |
| **Borne** (KLEMME) | Bornier à deux connexions (haut/bas) et champs IND (bornier), TYP, PER, NUM (numéro). Dans la boîte de dialogue des bornes (placement et double-clic), *Aspect* propose **Cercle** (comme avant) ou **Rectangle avec numéro** : 5 × 8 mm, NUM au milieu, IND à gauche, connexions en haut et en bas au centre. Des bornes placées à 5 mm d'intervalle (saisie ou grille 5) s'alignent et forment un bornier ; les coins et les milieux de côté fonctionnent avec l'accrochage aux objets. Décochez *afficher* pour IND sur les bornes 2, 3 … afin que la désignation (par ex. -X1) n'apparaisse qu'une fois devant la rangée. Les deux aspects peuvent être mélangés ; le plan de borniers, les réseaux et les contrôles se comportent de la même façon. Les anciens dessins restent inchangés (cercle). |
| **Câble** (KABEL) | Ligne horizontale avec une étiquette. Là où un fil vertical la croise, un repère de conducteur (L1, L2, L3, N, PE …) apparaît automatiquement ; la désignation peut être modifiée. |
| **Champ de coordonnées** (FELD) | Grille colonnes/lignes de la feuille, pour pouvoir donner les renvois sous la forme « feuille/colonne/ligne ». Dans la boîte de dialogue, choisissez **DIN A4** (287 × 164 mm, 6 × 4), **DIN A3** (395 × 252,59 mm, 8 × 5) ou saisissez vos propres valeurs. |
| **Texte de fonction** (FTEXT) | Texte multiligne ordinaire sur le calque **F-Text** (créé automatiquement). Il indique à quoi servent les appareils et bornes **situés derrière** son point d'insertion. Règle : un appareil ou une borne appartient au texte de fonction le plus proche **sur la même feuille** qui se trouve **à sa gauche (ou juste au-dessus)**. Dans le plan de borniers, un texte inchangé n'est affiché qu'au **premier** borne du bornier. Le texte apparaît tout à **droite** de la liste des appareils et du plan de borniers, dans la colonne **Fonction** (la colonne disparaît s'il n'y a aucun texte de fonction). |

### Symboles prêts à l'emploi

Le navigateur de blocs (**Blocs > Insérer un bloc/appareil**, touche `I`) contient une entrée
**symbols** (la bibliothèque de symboles) avec les symboles de base (contacts, boutons-poussoirs, fusibles, disjoncteurs,
bobines, moteurs, composants, compteurs …). Un double-clic place un symbole ; le masque et les broches
sont déjà préparés. La liste est dans `symbols/README.md`.

### Créer un appareil

1. Dessinez le symbole (lignes, rectangles …) et placez les **broches**.
2. Placez un **masque électrique** à côté. Choisissez le type : **appareil principal** (par ex. une
   bobine) ou **appareil auxiliaire** (par ex. un contact auxiliaire).
3. Sélectionnez symbole, broches et masque **ensemble**. Le rectangle de sélection doit aussi
   contenir tout le texte du masque, qui se trouve à gauche au-dessus du point d'ancrage du masque.
4. **Électricité > Créer un appareil à partir de la sélection…**, cliquez le point de base, saisissez un
   nom et confirmez appareil principal ou auxiliaire. L'appareil est désormais un bloc et est enregistré
   comme fichier dans le dossier des blocs.
5. Placez-le avec **Insérer un bloc/appareil (I)** ou **Blocs > Charger un bloc/appareil depuis un fichier…**.
   Lors de l'insertion, le programme demande IND, MAN, TYP, PER et le nom des broches.

Les appareils de **même IND** vont ensemble : l'appareil principal affiche dans REF les feuilles de
tous les appareils auxiliaires, un appareil auxiliaire affiche l'appareil principal. Vous obtenez ainsi,
par exemple, une bobine `K1` sur la feuille 3 et ses contacts `K1` sur les feuilles 5 et 6.
Chaque appareil ne peut contenir qu'**un seul** masque. Pour les appareils à plusieurs contacts, créez
chaque contact comme son propre appareil auxiliaire.

**Représentation unifilaire (second dessin) :** si vous dessinez le même appareil une fois
multifilaire (schéma de circuit) et une fois unifilaire (par ex. vue d'ensemble, plan de tableau
de distribution), cochez **Représentation unifilaire** dans la boîte de dialogue du symbole unifilaire
(masque d'appareil, bloc, borne ou câble). Un symbole marqué ainsi n'est **compté nulle part** : ni dans la liste des appareils,
ni dans la nomenclature, le plan de borniers, la liste des câbles ou des API, ni dans le réseau (listes
des connexions et des bornes), ni dans les renvois/REF, ni dans le contrôle du projet (« appareil principal en double »),
ni dans la numérotation automatique. Donnez au symbole unifilaire le même repère (IND) qu'au
multifilaire pour qu'ils puissent être rapprochés. Remarque : un appareil dessiné **seulement** en unifilaire n'apparaît dans aucune liste —
comptez-le avec un symbole multifilaire — ou cochez **Évaluer aussi la représentation unifilaire** dans la boîte de dialogue **Projet > Créer / mettre à jour la documentation...**. Les symboles unifilaires sont alors comptés, numérotés, contrôlés et pris en compte dans le réseau comme les symboles normaux, de sorte que les projets dessinés
**uniquement avec des symboles unifilaires** peuvent aussi être évalués. Si vous dessinez le même appareil en multifilaire **et** en unifilaire, laissez la case décochée,
sinon il apparaît deux fois. Le réglage est propre au projet et enregistré avec lui. Si vous changez le repère du symbole
multifilaire, changez-le à la main dans l'unifilaire.

**Nombre de pôles :** pour vos propres appareils, saisissez-le dans la même boîte de dialogue, dans le champ
**Nombre de pôles** (par ex. `3` ou `3+N` ; le champ est actif dès que la case est cochée). Il est
affiché exactement comme vous le tapez (`3`, `/3` ...) au-dessus du repère (IND) et peut être déplacé comme les autres textes du masque.
Les symboles de la bibliothèque « 12 Single-pole » ont à la place l'attribut **POLE** (un trait
sur la ligne avec le numéro) ; le champ n'apparaît alors pas deux fois.

### Fils

- **Automatique :** si deux points de connexion (broches, jonctions, bornes, renvois)
  se trouvent exactement l'un au-dessus de l'autre ou côte à côte et que leurs directions
  concordent, le fil rouge apparaît de lui-même. Il disparaît de nouveau si vous supprimez l'un des
  points.
- **À la main :** outil **Tracer un fil (LEITUNG)**, puis cliquez deux connexions l'une après
  l'autre.
- Si vous placez une broche, un appareil, une borne ou une jonction **sur** un fil existant, le fil
  est interrompu à cet endroit et relié.
- Double-cliquez une jonction pour modifier ses directions et son point.

### D'une feuille à l'autre : les renvois

**Chaîne sur plusieurs feuilles :** vous n'avez pas besoin de `L1.1`, `L1.2` ... Avec le même nom, une flèche *sortante* pointe vers la flèche *entrante* de la feuille **suivante**, une flèche *entrante* vers la *sortante* de la feuille **précédente** (de gauche à droite, dans l'ordre des feuilles). Ainsi, `L1` peut aller de la feuille 1 par 2 et 3 jusqu'à 4 et chaque flèche ne nomme que son voisin. S'il n'y a pas de partenaire correspondant dans cette direction, tous les autres emplacements portant ce nom sont affichés comme avant.

À la fin d'un fil, placez un **renvoi** (type *sortant* ou *entrant*,
direction, texte, par ex. `L1`) et placez-en un avec le même texte sur l'autre feuille. Le
destinataire (feuille/colonne/ligne) est affiché automatiquement. Pour les listes, KatieCAD suit le
circuit à travers ces paires quand il y a exactement une flèche sortante et au moins une
flèche entrante de même texte. Un potentiel comme `L1` qui apparaît à de nombreux
endroits reste un point final.

**Textes des renvois :** le repère (par ex. `L1`) et la note de destination (par ex. « (Feuille 6/1/D) ») se trouvent côte à côte sur une ligne par défaut, avec des hauteurs par défaut de 2,5 mm et 1,5 mm. Dans la boîte de dialogue des renvois (double-clic), vous réglez les deux hauteurs séparément. Les deux textes peuvent aussi être déplacés avec leurs poignées jaunes. **Réinitialiser les positions des textes** dans la boîte de dialogue les remet à leur position par défaut.

**Déplacer librement les textes :** les étiquettes des bornes, des masques (IND/MAN/TYP/PER/REF), des câbles, des broches et des blocs d'appareils peuvent aussi être déplacées. Sélectionnez l'objet et faites glisser la poignée jaune sur le texte. Pour un appareil inséré, le déplacement ne vaut que pour cette instance. **Réinitialiser les positions des textes** dans le menu du clic droit remet les textes à leur position par défaut. Depuis 1.0.3, le numéro de borne (NUM) est plus lisible à 1,75 mm.

### Bornes et câbles

- Placez les bornes côte à côte. **NUM** s'incrémente de lui-même au placement suivant. Vous n'avez besoin de saisir le bornier (IND) que sur la première borne d'une rangée ; les bornes à sa droite dans la même rangée le reprennent.
- Placez le **câble** en deux clics (début, fin) en travers des fils verticaux. La fin
  peut être prolongée plus tard avec sa poignée. CAB est le repère du câble (par ex. `W1`).

## 9. Générer la documentation

**Projet > Créer / mettre à jour la documentation…** crée des feuilles ordinaires dans le
projet, en **DIN A4** ou **DIN A3** (choisi dans la boîte de dialogue ; sur les zones A3, les textes et les hauteurs de ligne sont mis à l'échelle) :

- **page de garde** et **sommaire** (devant les feuilles de dessin)
- **liste des appareils**, **plan de borniers** et **plan des câbles** (derrière)
- **liste API** (liste des entrées/sorties de tous les modules API : automate, module, emplacement, type, adresse, type de données, symbole, commentaire, connexion, emplacement). Un bloc est un module API s'il possède l'attribut `SPS` = `DI`, `DO`, `AI` ou `AO` (les symboles de « 10 PLC » l'ont). Remplissez les champs supplémentaires avec **Modifier les attributs** : `STATION` (automate), `PLATZ` (emplacement) et, par voie, `VPn_SYM` (symbole) et `VPn_KOM` (commentaire). L'adresse est le texte de la broche (par ex. `I0.0`).
- d'autres listes (à activer dans la boîte de dialogue) : **liste des connexions** (de/vers avec câble et conducteur), **nomenclature** (regroupée par TYP avec fabricant, numéro de commande, désignation et repères), **liste des renvois**, **vue des potentiels** (L1, N, PE, +24 V ... avec toutes les connexions), **vue des connecteurs** (affectation des broches de tous les connecteurs ; les connecteurs sont des appareils avec un repère `X...` ou un type comme « connector »/« plug »), **liste des étiquettes** (appareils, bornes, câbles pour l'étiquetage) et **vue des révisions** (d'après le tableau des révisions des propriétés du projet)

Dans la boîte de dialogue, vous choisissez les feuilles, le modèle de cartouche, la **police des documents** (Arial par défaut, par ex. « ISO ») et les données du projet
(installation, client, numéro de commande, numéro de dessin, société, dessiné / vérifié par,
révision, date) ainsi que le format de feuille. Les feuilles de rapport sont entièrement reconstruites à chaque exécution. Les modifications
manuelles y sont perdues ; vos feuilles de dessin ne sont pas touchées.

- **Fabricant (champ `MAN`) :** outre IND, TYP et PER, le masque d'appareil possède le champ **MAN** (*fabricant*). Ordre de haut en bas : **IND, MAN, TYP, PER, REF**. Le fabricant apparaît dans la **liste des appareils** (colonne *Fabricant*) et dans la **nomenclature** : c'est d'abord le champ MAN de l'appareil qui est utilisé, s'il est vide, le fabricant du catalogue de pièces pour le TYP ; le même type de fabricants différents est listé sur des lignes séparées. **Bornes et câbles** ont aussi le champ MAN : sur une borne, il est dessiné sous IND et TYP et PER descendent d'une ligne ; sur un câble, il se trouve entre CAB et TYP (CAB remonte). Cela ne s'applique que si MAN est rempli, sinon bornes et câbles ont l'aspect habituel. Le fabricant apparaît dans le plan de borniers, le plan des câbles, la ligne du bornier de la liste des appareils et la nomenclature. **Dans les listes, les colonnes ont des noms lisibles :** *ID* (IND), *Fabricant* (MAN), *Désignation du type* (TYP) et *Puissance* (PER) ; les dessins gardent les abréviations. Un champ vide n'est pas dessiné ; les appareils déjà placés dans d'anciens projets restent tels quels jusqu'à ce que vous saisissiez MAN (double-clic sur l'appareil). **Mettre à jour des symboles existants :** `python tools/symbole_man_ergaenzen.py` (dans le dossier du projet) ajoute le champ MAN à chaque masque de `symbols/` et ne change rien d'autre ; avec `--pruefen`, il montre seulement ce qu'il modifierait.
- Les listes sont construites à partir des masques (IND/MAN/TYP/PER), des bornes, des câbles et des fils
  entre eux. Les emplacements sont donnés sous la forme feuille/colonne/ligne.
- **Catalogue de pièces (Projet > Catalogue de pièces...) :** attribuez fabricant, numéro de commande et désignation à chaque TYP. « Reprendre les types du dessin » saisit toutes les valeurs TYP trouvées, vous n'ajoutez que les détails. La nomenclature les utilise automatiquement. Le catalogue est stocké dans le fichier de projet.
- **Numéroter les appareils automatiquement (Projet > Numéroter les appareils automatiquement, commande `NUMMERIEREN`) :** les appareils dont le repère (IND) n'est qu'un préfixe (`-K`, `K?`) reçoivent le numéro libre suivant : `-K1`, `-K2` ... La numérotation continue après le plus grand numéro déjà utilisé dans tout le projet ; les numéros attribués ne changent jamais. Seul le symbole principal est numéroté, de haut en bas et de gauche à droite, pour tout le projet ou pour la feuille courante. Les parties auxiliaires (contacts) ne sont pas modifiées.
- **Exporter les listes en CSV…** écrit les mêmes tableaux pour Excel (séparés par des points-virgules,
  UTF-8).
- **Exporter les listes en fichier Excel…** (menu Projet) : choisissez les listes (liste des appareils, plan de borniers, plan des câbles, connexions, nomenclature, … ; le nombre entre parenthèses est le nombre de lignes) et obtenez **un fichier .xlsx avec une feuille par liste** (ligne d'en-tête figée en gras, filtre actif, largeurs de colonnes ajustées, colonnes numériques en nombres, désignations comme `001` restent du texte). Ni Excel ni une bibliothèque supplémentaire n'est nécessaire ; la sélection est mémorisée dans le projet.
- **Personnaliser les colonnes :** copiez `report_templates/geraete.example.json` et renommez-le
  en `geraete.json`, `klemmen.json`, `kabel.json` ou `inhalt.json`. Plus d'informations dans
  `report_templates/README.md`.

## 10. Import et export

- **Fichier > Importer…** lit des fichiers étrangers : DWG, DXF, PDF et images. Le programme reconnaît le format à l'extension du fichier, vous ne choisissez que le fichier. **Fichier > Exporter…** écrit le dessin en DXF ou DWG ; vous choisissez le type de fichier dans la boîte de dialogue d'enregistrement. (La sortie PDF et image se trouve sous *Imprimer*.)
  *[phrase inachevée dans l'original : « writes them. »]* Le DXF fonctionne directement. L'import DWG fonctionne sans logiciel supplémentaire (`ezdwg` intégré). Si un fichier DWG n'est pas lu proprement,
  enregistrez-le dans le programme d'origine en DXF ou en DWG plus récent (R2013/R2018). KatieCAD ne lance jamais de programme externe de lui-même. **Exporter en DWG** fonctionne aussi sans logiciel supplémentaire depuis 1.1.6 (écrivain intégré via `ezdwg`, licence MIT, format R2018, R2000 si nécessaire). L'écrivain ne connaît pas tous les types d'entités : ellipses, splines et polylignes à bombement sont écrites comme lignes ou arcs, les hachures seulement comme contour, les éléments non pris en charge sont omis — après l'export, KatieCAD indique ce qui a été concerné. Pour les livraisons importantes, exportez aussi en DXF et vérifiez dans le programme cible. Aucun programme de conversion externe n'est nécessaire ; seulement si vous avez installé LibreDWG (`dwg2dxf`) vous-même, KatieCAD l'utilise en secours à la lecture. **À l'import**, KatieCAD demande si le fichier doit être ouvert comme *nouveau dessin* ou *inséré dans le dessin courant* (la question est sautée quand le dessin est vide). Ensuite la vue zoome sur le dessin (Zoom étendu). Pour tester avec vos propres fichiers : `python tools/dwg_test.py`.
- **Quelle zone est exportée ?** *Exporter…* prend la zone où vous vous trouvez : dans la vue **modèle**, la zone du modèle ; dans une vue **présentation**, la présentation active comme feuille en mm (comme le DXF de projet : cadre de feuille, cartouche, contenu des fenêtres de vue ; le nom de la feuille est placé au-dessus). La barre d'état indique la zone exportée.
- PDF : voir section 6.

## 11. Raccourcis clavier

| Touche | Fonction |
|---|---|
| Ctrl+S | Enregistrer (dans un projet sans demander) |
| Ctrl+P | Imprimer |
| Ctrl+Z / Ctrl+Y | Annuler / Rétablir |
| Ctrl+C / Ctrl+X / Ctrl+V | Copier / Couper / Coller |
| Ctrl+Maj+C | Copier avec point de base |
| Ctrl+D | Dupliquer (avec décalage) |
| Suppr | Supprimer la sélection |
| Échap | Annuler / vider la sélection |
| F1 | Fenêtre listant tous les raccourcis clavier, actions souris et commandes (défilante, avec recherche ; aussi Aide > Raccourcis clavier et commandes) |
| F2 | Propriétés de la feuille (nom, emplacement de montage) |
| F3 / F7 / F8 / F9 | Accrochage aux objets / afficher la grille / ortho / accrochage à la grille |
| F4 | Afficher / masquer le panneau latéral |
| Ctrl+B | Insérer un bloc/appareil (sélection de bloc) |
| Ctrl+F | Rechercher et remplacer |
| G | Tout afficher (zoom étendu) |
| B / I / BL / X | Créer un bloc / insérer / sélection de bloc (comme I) / décomposer (dans la ligne de commande) |

Sur Mac, Cmd remplace Ctrl.

## 12. Astuces et questions fréquentes

- **« Créer un appareil à partir de la sélection » dit que le masque manque :** le masque doit faire
  partie de la sélection. Tirez le rectangle de gauche à droite et assez grand pour contenir tout son
  texte. Si le masque se trouve déjà dans un bloc placé, décomposez d'abord ce bloc
  (X).
- **Un fil n'est pas créé :** les points de connexion doivent être exactement alignés et leurs
  directions doivent concorder. Activez l'accrochage aux objets (F3) pour les atteindre précisément.
- **Les listes affichent « → L1 » ou similaire :** le circuit se termine à un renvoi sans
  contrepartie unique (ou à un potentiel comme L1). C'est voulu.
- **Les bornes apparaissent sans bornier :** saisissez IND sur la première borne de
  la rangée ; celles de droite le reprennent.
- **Une seule boîte de dialogue à la fois :** ouvrir une nouvelle boîte de dialogue ferme la précédente.
- **Sécurité :** les feuilles de dessin sont enregistrées automatiquement quand vous changez de feuille. Utilisez
  Ctrl+S pour enregistrer le projet à tout moment.

**Linux - barre de menus :** sous Linux, KatieCAD dessine sa propre barre de menus (un clic l'ouvre ; un clic ailleurs, Échap ou le passage à un autre programme la ferme ; F10 et les touches fléchées fonctionnent). Pour retrouver les menus Tk standard, démarrez avec `KATIECAD_NATIVE_MENU=1 python3 main.py`.

## Contrôle du projet / miroir de contacts
**Projet › Contrôler le projet…** contrôle toutes les feuilles de dessin : appareils principaux et câbles en double, parties auxiliaires sans appareil principal, bornes en double, renvois qui apparaissent plus de deux fois / sans contrepartie / avec deux fois le même type de flèche, et connexions de bornes ouvertes. Un double-clic sur un constat permet d'y aller. Marquez les renvois qui, volontairement, n'ont pas de contrepartie (alimentation, remise) avec **Remise / externe** dans la boîte de dialogue des renvois. De tels renvois ne pointent nulle part et ne sont jamais ciblés par d'autres : le même texte (par ex. `L1`) peut apparaître autant de fois que voulu, sans `L1.1`, `L2.1` ... La vue des potentiels les liste quand même.

**Miroir de contacts :** dans la boîte de dialogue de l'appareil (modifier les attributs ou le masque d'appareil), choisissez *Affichage* : liste de références, miroir de contacts à droite du symbole, ou — pour les relais — en dessous. Les contacts proviennent des parties auxiliaires de même repère ; l'ouverture/fermeture/commutation est déduite des étiquettes des broches (13/14, 21/22, 11/12/14 ...).

**Déplacer le miroir de contacts :** sélectionnez l'appareil — une poignée jaune apparaît en haut à gauche du miroir. Faites-la glisser pour déplacer librement le miroir ; la position reste relative à l'appareil. Elle est réinitialisée quand le mode d'affichage change.

## Propriétés (Ctrl+1)
**Du calque (couleur et épaisseur) :** la zone de couleur de la barre d'outils a une case à cocher **Du calque** à côté du champ de couleur, et la boîte de dialogue de couleur a un bouton **Du calque** : les nouveaux objets prennent alors la couleur du calque courant (le champ de couleur l'affiche). Dans la liste **Épaisseur**, **Du calque** est la première entrée : l'épaisseur de trait vient alors du calque et le suit. Avec une sélection, changer l'épaisseur l'applique aussi aux objets existants ; la fenêtre des propriétés (double-clic) et la palette des propriétés (Ctrl+1) offrent le même choix « Du calque ».

Édition › Propriétés ouvre une fenêtre pour la sélection courante, même mixte (lignes, textes, symboles ...) : calque, couleur (ou « Du calque »), type de ligne, épaisseur de trait et — dès que des textes en font partie — hauteur, angle et police du texte. Les valeurs différentes s'affichent comme *VARIÉ* ; une modification s'applique aussitôt à tous les objets sélectionnés.

## Échelle et symétrie
**Édition › Échelle** (commande `SCALE`/`SC`, aussi dans le menu du clic droit) : sélectionnez des objets, Entrée, choisissez le point de base, saisissez le facteur (par ex. `2` ou `0,5`). Les blocs sont mis à l'échelle avec leurs dimensions ; les éléments électriques à taille fixe (jonctions, renvois, masques, bornes) gardent leur taille et se déplacent seulement vers la nouvelle position.

**Édition › Symétrie** (commande `MIRROR`/`MI`, aussi dans le menu du clic droit) : sélectionnez des objets, Entrée, choisissez deux points de l'axe de symétrie (aperçu en direct), puis décidez si les originaux sont supprimés. Les textes restent lisibles (non symétrisés) ; les blocs, broches et étiquettes comprises, sont symétrisés correctement et restent des appareils.

## Projet entier en un seul fichier DXF / DWG
**Projet › Exporter le projet en DWG / DXF…** (type de fichier dans la boîte de dialogue d'enregistrement) évalue toutes les feuilles comme à l'impression (présentation avec cadre, cartouche et fenêtres de vue) et les place côte à côte dans un fichier DXF : 4 feuilles par ligne, puis une nouvelle ligne. Chaque feuille est sur son propre calque (`Blatt_01` ...), plus `Blattgrenze` et `Blattnamen`.

## Fenêtre d'informations et journal
Aide › À propos affiche le logo, la version et la licence. **Licence** ouvre le texte de la licence ; **Journal** ouvre le fichier de journal (`katiecad-log.txt` dans le dossier de configuration de KatieCAD) dans votre éditeur de texte par défaut – utile pour les rapports d'erreur. Le journal de la session précédente est conservé sous `katiecad-log.txt.old`.

## Emplacement de montage (propriétés de la feuille)
Appuyez sur **F2**, double-cliquez une feuille ou faites clic droit > *Propriétés de la feuille…* pour régler le nom de la feuille et son **emplacement de montage** (par ex. « Armoire UV1 »). Il s'applique automatiquement à chaque objet de la feuille et n'est pas copié dans les objets : changez-le et le cartouche et les listes suivent aussitôt. Dans le cartouche, un attribut avec l'étiquette `PLACE` (allemand `EINBAUORT`) l'affiche. Les listes des appareils, bornes et câbles reçoivent une colonne *Emplacement* (seulement si au moins une feuille a un emplacement) ; le même repère d'appareil à des emplacements différents compte comme des appareils différents. Les feuilles de rapport n'ont pas d'emplacement.

Cotations : **Insertion > Cotation > Cotation de rayon (DR)** et **Cotation de diamètre (DD)** — cliquez un cercle ou un arc, puis la position du texte.

## Plan de borniers : pontages
Ordre des colonnes : bornier, emplacement, type, **connexion haut, borne (NUM), pontage, connexion bas**, feuille/colonne/ligne. Les bornes du même bornier que vous reliez en haut ou en bas comptent comme un pontage : la colonne *Pontage* montre une ligne avec des points aux bornes reliées (les pontages qui se chevauchent utilisent des pistes séparées). La destination n'apparaît alors que sur la première borne du pontage ; les autres cellules restent vides. La colonne n'apparaît que s'il existe au moins un pontage.

Si une borne se trouve sur un rail de potentiel (par ex. PE ou N), « connexion haut/bas » n'affiche que le nom du potentiel. Condition : le réseau contient un point de connexion libre ou un renvoi nommé exactement comme la borne (NUM).

Dans le plan de borniers, chaque bornier (par emplacement) commence sur sa propre feuille ; les longues rangées se poursuivent sur les feuilles suivantes.
Les feuilles du plan de borniers portent le nom de leur bornier, par ex. « Klemmenplan X1 » (avec un emplacement, placé en premier : « Klemmenplan +1 -X1 » ; plusieurs feuilles pour un bornier : « ... X1 2/3 »). Cela vaut aussi pour le sommaire et le cartouche.

Dans les **propriétés de la feuille (F2)**, vous réglez aussi le **type de feuille** (schéma de circuit, vue de tableau, vue d'ensemble, présentation ou texte libre) et une **description**. Les deux apparaissent dans le sommaire ; sans saisie, le type est « Schéma de circuit » et la description reste vide.

## Importer un PDF
**Fichier > Importer…** (choisissez un fichier PDF) lit une page d'un PDF comme géométrie vectorielle (pas comme image). Choisissez la page et un **facteur d'échelle** (1 = taille papier ; saisissez 50 pour un tracé au 1:50). Si le PDF contient des calques (comme écrits par AutoCAD ou BricsCAD avec « inclure les informations de calque »), ils deviennent des calques KatieCAD de mêmes noms ; les calques masqués dans le PDF restent masqués. Sans calques, tout va sur le calque « PDF ». Importés : lignes, polylignes, rectangles, courbes, cercles, textes et remplissages pleins. Non importés : images raster (par ex. PDF numérisés), motifs de hachures, types de ligne en pointillés et détourage. Les textes arrivent parfois en fragments. L'import n'utilise que des bibliothèques sous licence libre (pypdf) ; KatieCAD reste sous licence BSD-3-Clause. Pour l'essayer depuis les sources : `pip install pypdf` (aussi dans `requirements.txt`).

## Importer une image

Remarque : l'export PDF écrit les calques KatieCAD comme calques PDF. Vous pouvez les activer ou les désactiver dans les lecteurs PDF et réimporter un tel PDF dans KatieCAD avec les mêmes noms de calques.
**Fichier > Importer…** (choisissez un fichier image) insère une photo ou un graphique (PNG, JPG, BMP, GIF, TIFF). L'image est stockée dans le dessin, le fichier d'origine n'est donc plus nécessaire. Redimensionnez avec la poignée de coin jaune ou **Échelle** ; déplacer, tourner et symétriser fonctionnent comme pour les autres objets. Les grandes images sont réduites à 2400 pixels au maximum sur le grand côté. Les images apparaissent dans la sortie PDF ; à l'export DXF, le fichier image est écrit à côté du fichier DXF. L'export DXF du projet n'inclut pas les images.

