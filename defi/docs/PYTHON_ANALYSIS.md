# Analyse de defi_ton_pote.py et contrat du portage

## Ce que contient réellement le programme

Le fichier Python contient environ 3 350 lignes et une classe `JeuDefi` qui concentre navigation, entrées, simulation, rendu et persistance. Il utilise Pygame avec une surface logique de 1 000 × 700. Les menus basculent entre accueil, création, campagne, bibliothèque, éditeur, partage, arcade, parcours et résultat. La pause est indépendante de ces états. Les parties sont locales : le « défi à un pote » consiste à transmettre un code, pas à jouer en réseau.

Le précédent dossier web `defi/` contenait Cosmo Dash, une collecte de huit étoiles avec des astéroïdes. Cette mécanique ne correspondait pas au Python. Le portage remplace ce prototype dans le même dossier, garde npm, le lockfile et Phaser 4, et adapte le workflow Pages existant.

Deux dépendances Python ne définissent pas les règles des parcours : `realisme_visuel.py` fournit textures et atmosphère ; `cache_cache_3d.py` est un autre jeu lancé de façon synchrone par un bouton du menu création. Ce dernier n’est pas porté ici. Les graphismes Pygame et l’atmosphère sont remplacés par des dessins Phaser locaux, sans ressources réseau ni reproduction pixel pour pixel.

## Arcade : survivre et optimiser le score

Les fonctions `normaliser_code`, `code_vers_graine`, `code_defi_du_jour`, `lancer`, `mettre_a_jour`, `creer_projectile` et `lancer_esquive` définissent cette boucle.

- Un code de quatre caractères, ou un ancien code de six, est nettoyé en majuscules dans l’alphabet **ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789**. La conversion accumule les indices en base 36. Ce n’est pas l’alphabet numérique habituel de `parseInt(code, 36)`.
- Le défi quotidien prend les quatre premiers octets du SHA-256 de la date locale `YYYY-MM-DD`, chacun modulo 36. Deux joueurs dans des fuseaux dont la date diffère peuvent donc recevoir des défis différents, comme dans le Python.
- La partie dure 45 secondes, commence avec trois vies et une seconde d’invulnérabilité. Le personnage se déplace à 310 pixels/s, en normalisant les diagonales, et reste dans x = 40…960 et y = 127…650.
- L’esquive dure 0,19 s, multiplie la vitesse par 2,45, mémorise la dernière direction et se recharge en 1,05 s. Elle garantit au moins 0,24 s d’invulnérabilité.
- Les projectiles apparaissent sur l’un des quatre bords, visent la position du joueur au moment de leur création et affichent un avertissement de 0,34 s. « Traqueur » ne signifie donc pas guidage permanent.
- Les familles traqueur / éclat / spirale ont des probabilités 5/10, 3/10 et 2/10. Leurs vitesses augmentent avec le temps ; seule la spirale tourne, de 115 degrés/s. Les rayons sont respectivement 10–13, 7–9 et 12–15 pixels.
- Le premier projectile arrive à 1,1 s. L’intervalle est tiré entre 0,75 et 1,2 fois `max(0.52, 1.45 - temps × 0.018)`.
- Au plus deux fragments restent présents simultanément. Le premier arrive à une seconde, puis l’intervalle est compris entre 2,2 et 3,1 secondes. Une collecte rapporte 150 points, avec bonus de combo de 30 points par palier, plafonné à 150 ; le combo se poursuit si moins de quatre secondes séparent les collectes.
- Un contact enlève une vie, remet le combo à zéro, vide les projectiles et protège 1,35 s. Une collision supprime aussi le projectile si le joueur est invulnérable.
- Le score est ensuite relevé au minimum `floor(temps × 12) + fragments × 150`. Ce n’est pas une addition systématique du temps au score de combo. En fin de partie, les vies restantes ajoutent 100 points chacune, une seule fois.

`random.ts` reproduit le MT19937 de CPython, l’initialisation par entier, `random()` sur 53 bits et le rejet utilisé par `randint`. Des valeurs de référence produites par Python vérifient les tirages. Cela conserve la suite aléatoire ; cela ne promet pas un replay identique entre une boucle Pygame et un navigateur, car les instants de collecte et les trajectoires dépendent aussi des entrées et du pas de simulation.

## Parcours : modèle et physique

Une carte contient 40 colonnes × 11 lignes de cases de 48 pixels, soit 1 920 × 528 pixels. Le format stocke `tiles`, `start`, `goal`, `monstres`, `theme`. Le départ et l’arrivée sont des coordonnées séparées de la grille. Les monstres sont une liste de paires de coordonnées.

| Valeur | Élément | Comportement |
| --- | --- | --- |
| 0 | Vide | Traversable |
| 1 | Sol | Collision des quatre côtés |
| 2 | Plateforme | Atterrissage seulement par-dessus ; traversable en montant |
| 3 | Pics | Zone dangereuse réduite de 4 px sur les côtés et 12 px en haut |
| 4 | Checkpoint | Réapparition à cet endroit, +250 points une seule fois |
| 5 | Ressort | Impulsion verticale de −690 px/s, verrouillée jusqu’à sortie du contact |
| 6 | Gemme | +500 points ; facultative pour gagner |
| 7 | Cœur | +250 points et une vie, avec plafond à cinq |

Le personnage mesure 28 × 38 pixels. La marche vise 270 px/s, la course 360. L’accélération est de 2 300 au sol et 1 150 en l’air ; sans direction, le freinage est de 2 600 au sol et 260 en l’air. Le saut impose −510 px/s. Le maintien du bouton utilise une gravité de 900 durant la montée, autrement 1 450 ; la chute est plafonnée à 780 px/s. Le délai de tolérance après avoir quitté un bord (« coyote time ») vaut 0,1 s et la mémorisation d’un appui avant atterrissage vaut 0,14 s.

Un monstre recherche un support dans sa case ou juste dessous, puis étend sa patrouille sur les cases adjacentes portant sol/plateforme, sans obstacle solide ou pic à hauteur de déplacement. Il avance à 82 px/s et rebondit aux bornes. Sans support, il reste sur place. Le rectangle de collision effectif du Python est 34 × 34, malgré d’autres constantes de dessin plus grandes.

Une mort coûte une vie et replace le personnage au dernier checkpoint, avec vitesses et état de saut réinitialisés et une seconde de protection. Les gemmes/cœurs déjà collectés ne réapparaissent pas. Le chronomètre continue après la mort. Toucher la porte gagne sans imposer de collecte ; le bonus final vaut `max(0, 10000 - round(temps × 50))`. Le record de parcours est le plus petit temps gagnant en millisecondes, pas le score.

La simulation TS est autonome, avec collisions rectangulaires résolues une seule fois et pas fixe de 1/120 s. Phaser assure le rendu et le pointeur ; on ne superpose pas un second moteur physique Arcade à ces règles. Le choix préserve les plateformes unidirectionnelles, les impulsions et l’ordre des contacts du script. Les positions restent flottantes : le Python arrondissait les déplacements à chaque frame, ce qui rendait la vitesse dépendante de sa fréquence. Les longues interruptions sont mises en pause et le rattrapage par frame est borné.

## Création des niveaux : mêmes cartes, mêmes principes

`niveau_depart()` crée une démo fixe : sept colonnes de trous, plateformes sur plusieurs hauteurs, six pics, treize gemmes, deux cœurs, deux checkpoints, un ressort et quatre patrouilleurs. `demoLevel()` reproduit toutes ses cellules.

`niveau_carte_base(numero)` est déterministe et ne fait aucun tirage aléatoire. Son numéro est borné entre 1 et 12 :

1. Le nombre de groupes de trous est `1 + floor((n−1)/2)`. Leur départ est réparti de 8 à 32. À partir du niveau 7, les groupes d’indice pair font deux cases de large.
2. Le nombre visé de pics est `min(14, n+2)`. Les cibles sont réparties de 4 à 35. Le générateur choisit la case disponible la plus proche, avec préférence pour une séparation d’au moins deux colonnes. Si nécessaire, il relâche cette séparation. Les égalités favorisent la colonne la plus petite.
3. Le nombre de monstres est `1 + floor(n/2)`. Ils sont répartis entre 5 et 34, hors trous/pics, avec une distance préférée de trois colonnes, puis un repli vers les places restantes.
4. `floor(n/2)` plateformes sont placées à la ligne 8, près de cibles réparties de 6 à 34, hors trous.
5. Deux gemmes restent aux colonnes 2 et 37. Dès le niveau 5, deux cœurs apparaissent aux colonnes 3 et 36.
6. Les checkpoints sont placés près de 13 puis 27, hors trous/pics/monstres. Bien que le bloc Python soit conditionné par `n >= 4`, son calcul entier donne effectivement zéro checkpoint avant le niveau 6, un aux niveaux 6–11, deux au niveau 12.
7. Le départ est [1,9], l’arrivée [38,9], le biome de campagne reste prairie. Changer le biome modifie le rendu ; cela n’ajoute pas de glissade ou de dégâts de lave.

La fonction `pyRound` respecte l’arrondi au pair de Python, qui diffère de `Math.round` aux demi-entiers. Les tests comparent **la totalité des cellules et métadonnées** de la démo et des 12 cartes à des fixtures extraites des fonctions Python. Il n’y a ni remplacement des cartes par un générateur « similaire », ni équilibrage silencieux. Une politique automatique « courir et sauter en permanence » perd même sur le niveau 1 : elle ne constitue pas une preuve d’impossibilité du parcours et n’a pas été utilisée pour modifier les niveaux.

## Éditeur et protocole partagé

L’éditeur permet peinture à la souris ou au tactile, gomme, départ/arrivée, dix outils de blocs/points et monstre, quatre biomes, défilement horizontal, nom, annulation/rétablissement sur 40 modifications, test et retour au brouillon intact. Le départ et l’arrivée sont protégés des outils ordinaires. Déplacer le départ dégage sa case et lui ajoute un sol sûr si nécessaire. Effacer un monstre conserve d’abord le bloc situé dessous.

La bibliothèque est enregistrée dans `localStorage` sous une clé propre au jeu, avec schéma versionné, au lieu des fichiers du répertoire Windows AppData. Les cartes en cours peuvent être temporairement injouables et restent rechargeables ; le test et l’export exigent une carte valide. Un format de sauvegarde inconnu ou corrompu est préservé au lieu d’être écrasé automatiquement. Les erreurs de quota laissent jouer et proposent l’export. Les records sont locaux, sans classement distant ni protection anti-triche.

Le format P4 est conservé : 440 octets de cases, quatre octets départ/arrivée, deux octets big-endian pour le nombre de monstres, deux octets par monstre, puis un octet de biome. Le tout est compressé en zlib et encodé en base64 URL sans remplissage, préfixé `P4-`. P3 omet le biome ; P2 omet aussi les monstres ; P1 transporte du JSON compressé. Les API natives CompressionStream/DecompressionStream évitent une dépendance de compression. La chaîne exportée peut différer du Python (niveau/implémentation de compression), mais les données décodées restent identiques et compatibles.

Les entrées sont limitées à 2 000 caractères et la décompression à 5 000 octets. On vérifie dimensions, valeurs entières, départ sûr, arrivée, biome, bornes et unicité des monstres. Cette validation structurelle ne cherche pas à résoudre le niveau : un auteur peut créer un parcours impossible, comme en Python.

## Défauts et limites de la source

- Deux en-têtes consécutifs `def dessiner_icone_palette(...)` aux lignes 576–577 rendent le fichier invalide syntaxiquement. Le fichier utilisateur n’a pas été modifié. Le générateur de fixtures retire uniquement ce doublon en mémoire avant d’extraire les fonctions pures avec `ast`, sans importer Pygame ni exécuter le jeu.
- Les constantes et icônes de cracheur/chargeur/sauteur apparaissent dans la palette, mais `changer_case` ne gère que l’outil monstre 10. Les codes ne transportent aucun type de monstre et `initialiser_monstres` ne crée que des patrouilleurs. Le portage n’affiche donc pas des variantes dépourvues de règles.
- Le code P4 ne stocke pas le nom local de la carte. Le portage conserve cette convention.
- Le Python affiche seulement les sept fichiers de parcours les plus récents ; le navigateur expose toutes les cartes enregistrées.
- Aucun mode de coopération réseau, génération aléatoire des parcours, simulation 3D, audio ou backend n’a été inventé.

## Livraison et preuves

La version installée du moteur est Phaser 4.2.1. Les méthodes Graphics, le pointeur et le ScaleManager sont vérifiés dans ses déclarations et son code local. Les règles ne dépendent ni de Phaser ni du DOM. Un recalcul de la taille du parent et des bornes du canvas est effectué après les changements de disposition, pour conserver précision de peinture et dimensions sur mobile.

La PWA embarque moteur, code, styles, icônes et niveaux. Le manifest, les assets et le worker utilisent la même base `/jeux/`. Le cache porte une identité propre au jeu ; les mises à jour attendent une action explicite, refusée pendant la partie. Le workflow utilise npm ci, contrôle TypeScript, Vitest et build avant l’upload ; seuls les jobs de déploiement ont les permissions Pages. Aucun push ou déploiement n’a été effectué pendant ce travail.

Voir `VALIDATION.md` pour les essais réellement exécutés et `README.md` pour les commandes. Références officielles vérifiées : [Phaser 4.2.1](https://github.com/phaserjs/phaser/releases/tag/v4.2.1), [mise à jour PWA sur confirmation](https://vite-pwa-org.netlify.app/guide/prompt-for-update.html), [workflow Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
