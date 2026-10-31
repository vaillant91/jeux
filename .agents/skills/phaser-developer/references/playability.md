# Jouabilité, présentation et performance

## Tranche jouable

Vérifier une boucle entière avec un objectif compréhensible, une action réactive, une réussite ou un échec perceptible et une possibilité de rejouer. Montrer les contrôles au moment utile. Donner un feedback aux actions importantes : animation, couleur, son ou mouvement, en respectant le style demandé.

Pour une mécanique exigeant de la précision, envisager tolérance d'entrée, buffering ou coyote time selon le genre ; ne pas appliquer ces techniques à tous les jeux. Garder les valeurs d'équilibrage modifiables sans toucher aux scènes.

## Affichage et accessibilité

- Choisir résolution logique et stratégie de scale selon le genre. `FIT` peut préserver le terrain ; une stratégie de resize demande de recalculer layout, caméra et coordonnées d'input. Tester les deux orientations visées et le redimensionnement.
- Vérifier mobile étroit, desktop, fortes densités de pixels et zones sûres. Éviter d'étirer le canvas par CSS indépendamment de son système de coordonnées.
- Afficher texte et boutons à une taille utilisable au tactile. Ne pas transmettre une information indispensable uniquement par couleur ou audio.
- Utiliser des éléments DOM sémantiques pour menus, réglages et boîte de mise à jour lorsque cela améliore clavier, focus et lecteur d'écran. Préserver un focus visible et restaurer le focus après fermeture d'une boîte.
- Respecter une préférence de mouvement réduit pour effets non essentiels : secousses, flashes, transitions. Exposer pause et mute. Ne pas annoncer le contenu d'un canvas comme intégralement accessible sans parcours testé.
- Vérifier le rendu réel des polices après chargement et hors ligne ; éviter un changement de police qui coupe les labels.

## Performance mesurée

Définir l'appareil cible avant de fixer un budget. Pour une cible à 60 Hz, environ 16,7 ms est le budget total d'une frame, pas une garantie du moteur. Mesurer frame time, mémoire, volume de téléchargement et délai jusqu'à la première interaction sur un scénario représentatif.

Commencer par les causes observables : allocations et textes recréés chaque frame, nombre de corps actifs, particules, effets plein écran, taille des textures, surdessin et densité de pixels. N'ajouter atlas, pool, réduction de résolution ou objet GPU spécialisé qu'en lien avec la mesure.

Profilage : comparer la même scène, le même appareil et une durée similaire avant/après. Plusieurs restarts ne doivent pas produire une croissance persistante du nombre d'objets/handlers ; la mémoire brute seule peut fluctuer avec le GC. Vérifier perte/restauration du contexte WebGL si le jeu dépend de ressources graphiques personnalisées.

Une émulation mobile dans un navigateur desktop ne prouve pas la performance ni le comportement audio sur un téléphone réel. Rapporter cette limite explicitement.
