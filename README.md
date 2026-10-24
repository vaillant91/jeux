# Defi ton pote

Jeu Pygame avec un parcours de plateforme, un editeur de niveaux partageables
et un petit defi arcade. Dans l'editeur, place des sols, des plateformes et des
pics, puis choisis le depart et l'arrivee. Le code genere contient la carte :
un ami peut le coller dans le menu pour jouer au meme parcours.

## Lancer le jeu

```powershell
.\.venv\Scripts\python.exe .\defi_ton_pote.py
```

- **Jouer la carte de base** : campagne de 12 niveaux de difficulte
  croissante, avec de nouveaux trous, pics et monstres a chaque etape.
- **Creer mon parcours** : ouvre l'editeur.
- Outils d'editeur : gomme (0), sol (1), plateforme (2), pics (3),
  checkpoint (4), ressort (5), gemme (6), coeur (7), monstre (M),
  depart (8), arrivee (9), rampe montante et rampe descendante (palette). Le coeur rend une vie, jusqu'a cinq au total ;
  les monstres patrouillent sur les plateformes et font perdre une vie au contact.
- **Ctrl+Z / Ctrl+Y** dans l'editeur : annuler ou refaire une modification.
- **SAUVER** ou **Ctrl+S** : conserver le brouillon sur cet ordinateur ;
  **N** : repartir du parcours de demonstration.
- **Defi arcade** : esquive les projectiles et ramasse les fragments pendant
  45 secondes.
- Dans l'editeur, clique une case pour poser le bloc selectionne. Le clic droit
  efface une case ; les touches 0 a 6, 8 et 9 selectionnent aussi les outils.
- **A/D** ou la molette : faire defiler la carte dans l'editeur.
- **CODE** : genere un code partageable et le copie dans le presse-papiers.
- **TEST** : jouer son parcours ; **MENU** : revenir au menu principal.
- Dans le parcours, fleches ou ZQSD pour bouger, Espace pour sauter et Echap
  pour mettre en pause. Le saut est tolerant juste apres avoir quitte une
  plateforme ; les gemmes augmentent le score, les checkpoints servent de
  points de reprise et les ressorts propulsent le joueur.
- Dans le menu, clique dans la zone de code, colle le code de ton ami avec
  Ctrl+V puis clique sur **Jouer le code** (ou appuie sur Entree).
- Dans le defi arcade, fleches ou ZQSD pour bouger, Espace pour esquiver et
  P/Echap pour mettre en pause.

Le partage fonctionne en copiant un code texte, sans serveur ni comptes en
ligne. Les records du defi arcade sont conserves localement sur l'ordinateur.
Le meilleur temps de chaque parcours est egalement garde localement. Le dernier
brouillon est recharge quand tu ouvres l'editeur sur le meme ordinateur.

---

# Les ruines de Valombre

Jeu d'aventure realise avec Pygame. Explore les quatre royaumes,
ouvre les coffres pour trouver des armes et des boucliers, accomplis les quetes
et rejoins les ruines au bout de la carte. Le monde est rendu en perspective a
la troisieme personne, avec une camera qui suit le heros et peut etre tournee a
la souris. Les royaumes ont leurs propres decors, et les personnages sont animes.

## Commandes

- Fleches ou ZQSD : se deplacer par rapport a la camera
- Maintenir le clic droit et bouger la souris : tourner la camera
- Espace : attaquer avec l'arme equipee ou tirer une fleche
- E : ouvrir un coffre, parler a un habitant ou prendre la relique
- I : ouvrir/fermer l'inventaire
- Haut/Bas puis Entree : choisir et equiper une arme ou un bouclier
- F : manger une ration
- Maintenir Maj : escalader les pentes raides ; l'endurance se recharge au repos
- Maintenir Ctrl : avancer accroupi, ralentir et reduire la detection ; dans les
  hautes herbes, se cacher completement des monstres
- X : esquiver ; l'esquive consomme de l'endurance et rend brièvement invulnerable
- C : attaque speciale ou fleche chargee ; consomme de l'endurance
- Echos secrets : cherche les reliques Zelda et les clins d'oeil aux mangas
- F5 : sauvegarder la partie ; F9 : charger la derniere sauvegarde
- Echap : quitter

Les coeurs en haut a gauche indiquent les vies restantes ; la barre verte
montre l'endurance disponible pour l'escalade, et la jauge doree indique la faim.

Les arcs consomment des fleches et les arcs ainsi que les epees infligent des
degats importants. La defense de chaque bouclier equipe reduit les degats des
attaques ennemies, et peut bloquer entierement les coups faibles. Grimpe les
pentes enneigees en marchant ; Maj permet d'escalader les
pentes plus raides au prix de l'endurance, mais les falaises restent infranchissables.
Quand le heros tombe, l'ecran affiche « GAME OVER ». Appuie sur Entree pour
reprendre au meme endroit avec ses armes, son equipement et sa progression ;
une courte invulnerabilite lui permet de reprendre le combat. Les coffres et
les ennemis peuvent fournir des armes :
dagues, lances, masses, epees, arcs et arbaletes ont des degats, une portee,
une cadence ou une vitesse de projectile qui leur sont propres. Les ennemis
puissants et les boss ont davantage de chances de laisser une arme de haut palier.
Les camps ont un feu de camp anime entoure de pillards, d'araignees, de
chauves-souris et de gardes, ainsi qu'un boss dont la puissance augmente selon
la region. Les ennemis doivent reperer le heros dans leur champ de vision et
sans obstacle avant de le poursuivre ou de l'attaquer ; un point d'exclamation
signale leur alerte. Accroupis-toi pour reduire la portee et l'angle de detection
des monstres ; les hautes herbes te cachent completement si tu restes accroupi
a proximite. Les rencontres ordinaires ont ete reduites et plus largement
reparties sur la carte ; chaque grotte garde deux
adversaires et un gardien puissant. Les boss ont une barre de vie, une zone de
collision plus large et signalent leurs attaques avant de frapper : cherche une
ouverture et esquive pendant leur charge. Les loups annoncent aussi leur bond,
qui peut etre evite en s'eloignant de la zone visee. X permet une esquive rapide, tandis que
C declenche une attaque speciale puissante (ou une fleche chargee avec un arc).
Le Temple des runes, a l'est, ajoute un sceau a ouvrir dans l'ordre Lune, Soleil,
Etoile, des pieges a pics alternant leurs phases et un chevalier gardien. La quete des camps demande de vaincre
deux chefs, dont un centaure, un cyclope ou un geant. Le dragon final possede
trois tetes et apparait dans la quete des cimes. Les trois grottes ont leurs
propres salles, monstres et tresors : appuie
sur E a l'entree pour descendre, puis E pres de la sortie pour remonter. Parle
aux habitants des villages pour accepter les quetes de combat, de repaire et
d'exploration. Chaque village comprend six maisons plus grandes, une place
centrale propre a son biome (puits, arbre communautaire, citerne ombragee ou
abri de montagne) et des habitants aux tenues et accessoires de travail
distinctifs. Quatorze coffres sont repartis sur la carte, avec armes, boucliers,
fleches et gemmes. Les anciennes sauvegardes recuperent les coffres manquants
sans refermer ceux deja ouverts. Les facades, toitures et materiaux des maisons
varient aussi selon le climat local. Quand une quete est rendue, une courte scene
de celebration se lance : le heros brandit son epee, bondit et la plante dans
le sol avant de recevoir sa recompense. E, Espace ou un clic gauche permet de
passer a la suite, et Echap permet d'ignorer la scene. Des rations sont
dissimulees dans chaque region et dans les grottes. La mini-carte indique aussi
les camps et les entrees des grottes.

La carte a ete etendue a 160 x 120 cases, soit quatre fois sa superficie
precedente. Les quatre royaumes et leurs quetes gardent leurs emplacements ;
de nouveaux sentiers, forets, lacs, rivieres et reliefs prolongent l'exploration
vers l'est et le sud. La mini-carte s'adapte a la taille du monde, y compris
pour les anciennes sauvegardes.

Le heros est un aventurier elfique original, avec tunique verte, bonnet vert
pointu, silhouette un peu plus fine, cheveux clairs, oreilles pointues,
bouclier, cape animee, sac a dos detaille et equipement d'exploration. Les
courbes du visage, les coutures de la tunique, les renforts des manches et les
details de la capuche enrichissent sa silhouette. Il s'incline et adopte une
posture basse lorsqu'il s'accroupit. Sa tenue suit le rythme de ses pas et
respire legerement lorsqu'il est immobile. Des vols
d'oiseaux battent des ailes et traversent le ciel au-dessus des montagnes.
Le rendu ajoute une lumiere solaire douce, des montagnes atmospheriques,
une brume d'horizon fondue selon le biome, un relief mieux ombre et davantage
de details au sol et sur l'eau.
L'eclairage du monde evolue aussi au fil d'un cycle jour-nuit, avec crepuscules,
soleil mobile, lune, etoiles et teintes adaptees a l'heure.
Les saisons changent les teintes du terrain et des feuillages ; vents, pluie,
orages et neige passent sur le monde et sont annonces dans l'interface.
Les habitants donnent des indices sur 47 echos caches : 29 reliques liees aux
jeux Zelda, de The Legend of Zelda et Zelda II jusqu'a Echoes of Wisdom, avec
A Link to the Past, Link's Awakening, Ocarina of Time, Majora's Mask, Oracle of
Ages/Seasons, Four Swords et Four Swords Adventures, The Minish Cap, Twilight
Princess, The Wind Waker, Phantom Hourglass, Spirit Tracks, Skyward Sword,
A Link Between Worlds, Tri Force Heroes, Breath of the Wild, Tears of the
Kingdom, ainsi que quelques detours par Game & Watch, Ancient Stone Tablets,
Link's Crossbow Training, Hyrule Warriors et ses episodes Age of Calamity
et Age of Imprisonment, Cadence of Hyrule et Tingle's Rosy Rupeeland.
S'y ajoutent trois reliques originales pour chacun de ces mangas :
One Piece, Dragon Ball, One Punch Man, Fairy Tail, Fullmetal Alchemist et
Dr. Stone. Les petits autels sont reperables sur la mini-carte ; rassemble-les
tous pour obtenir une recompense bonus. Ce sont des clins d'oeil a des themes
d'aventure, sans reproduction des personnages, dessins ou dialogues.

La sauvegarde conserve la progression, l'inventaire, les quetes, les camps,
les coffres, les ennemis, les echos secrets et l'etat des grottes. Les
anciennes sauvegardes recuperent aussi les nouveaux echos sans faire reapparaitre
ceux deja ramasses. Le chargement restaure la position du joueur dans les grottes.

## Mode cache-cache

Le menu propose aussi un cache-cache en vue a la troisieme personne sur une carte
plus vaste. Ton role, cacheur ou chasseur, est attribue automatiquement contre
des personnages controles par le jeu. Le chasseur marque les cacheurs avec des tirs
non graphiques. L'editeur
permet de creer une carte avec des murs et des cachettes ; les anciennes cartes
personnalisees sont agrandies automatiquement au chargement.

Le cache-cache ajoute un cycle de lumiere, des materiaux texturés, des ombres,
une meteo changeante et une camera avec inertie. Les bots utilisent un champ de
vision, suivent les bruits de pas et recherchent une derniere position connue ;
leurs chemins contournent les murs. Maintiens **Maj** pour courir et **Ctrl**
pour avancer accroupi en faisant moins de bruit. Une jauge signale le bruit
recent quand tu joues le cacheur. Le parcours de plateforme partage aussi les
materiaux, le ciel evolutif et les particules, avec pluie et neige.
