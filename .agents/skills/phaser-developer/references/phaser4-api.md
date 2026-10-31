# Vérifier les API Phaser 4

Références consultées lors de l'écriture du pack : 24 octobre 2026. Cette date n'est pas une contrainte de version pour les futurs projets.

## Ordre de preuve

1. Version exacte du lockfile et paquet installé (`npm ls phaser` si npm).
2. Déclarations TypeScript et code du paquet installé pour la méthode précise.
3. Documentation, changelog et exemples officiels correspondant à cette version ; préférer un tag au `master` évolutif.
4. Micro-exemple compilé puis exécuté dans le navigateur quand le comportement de rendu est incertain.

Si le réseau est indisponible, travailler à partir des types et sources locaux, signaler ce qui n'a pas été vérifié. Ne pas mettre à jour le moteur uniquement pour faire fonctionner un exemple trouvé en ligne.

## Zones où les exemples Phaser 3 sont trompeurs

Le rendu v4 utilise des Render Nodes et les effets/masques ont été remaniés. Les anciens pipelines WebGL, effets, shaders, tint et textures demandent une vérification spécifique. Le fait qu'un tutoriel partage `Scene`, `preload` et `create` ne garantit pas la compatibilité de ses extensions graphiques.

Ne pas recopier un remplacement de méthode de mémoire. Lire la section concernée du [guide officiel de migration](https://github.com/phaserjs/phaser/blob/master/changelog/v4/4.0/MIGRATION-GUIDE.md) puis vérifier le tag installé. Pour les plugins tiers, confirmer la compatibilité v4 et leur maintenance avant de les ajouter. Les objets GPU spécialisés ne sont pas des remplacements automatiques des sprites interactifs ou physiques.

Le dépôt officiel contient des [skills Phaser spécialisés](https://github.com/phaserjs/phaser/tree/master/skills). Lorsqu'un sous-système complexe l'exige, consulter seulement le fichier pertinent à la version utilisée ; ne pas importer tout le catalogue ni déléguer automatiquement.

Sources : [releases](https://github.com/phaserjs/phaser/releases), [documentation officielle](https://docs.phaser.io/), [cycle des scènes](https://docs.phaser.io/phaser/concepts/scenes).
