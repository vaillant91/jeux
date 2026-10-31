# Stratégie Vitest

## Choisir l'environnement

| Risque | Preuve adaptée |
| --- | --- |
| Score, génération, victoire/défaite, progression | Vitest `node`, fonctions métier et données |
| Version/validation/migration de sauvegarde | Vitest `node`, adaptateur stockage minimal |
| Menu DOM, messages, focus logique | DOM simulé pour logique ; navigateur pour comportement réel |
| API Phaser, collisions, renderer, input, audio | Navigateur réel avec le moteur |
| Cache, scope SW, update, sous-chemin | Build de production servi, navigateur avec service worker |

`jsdom` et `happy-dom` ne reproduisent pas un renderer WebGL ni un cycle de vie PWA. Éviter d'importer le point d'entrée Phaser dans les tests métier. Si cet import est nécessaire à un test de score, examiner la frontière entre règles et moteur.

Vitest Browser Mode peut tester du code dans un navigateur réel ; consulter la configuration correspondant à la version installée et choisir un provider compatible. Un provider Playwright ne transforme pas automatiquement ces tests en recette E2E du site construit. Pour navigation, plusieurs onglets, offline et service worker sur un build, utiliser si nécessaire un runner E2E dédié comme Playwright ou les outils navigateur déjà disponibles. Garder Vitest comme socle des tests unitaires.

## Cas à fort rendement

- État initial, borne zéro, seuil exact de victoire/défaite, événement reçu deux fois, action après fin de partie.
- Pause et reprise sans progression indue, restart sans ancien score ni effet différé, fin simultanée de deux événements.
- Génération reproductible avec seed ; contraintes du niveau sur plusieurs seeds fixes. Utiliser une bibliothèque de tests génératifs seulement si l'espace des cas le justifie.
- Sauvegarde absente, JSON invalide, champs invalides, migration connue, version future, stockage qui lance une exception.
- Input appui/maintien/relâchement ; mappings clavier et tactile convergeant vers la même action.
- Nettoyage via un adaptateur vérifiable, puis test navigateur de restart ; un mock seul ne prouve pas l'absence de fuite du moteur.

Injecter un faux temps ou un générateur de nombres à la frontière métier plutôt que modifier globalement `Date.now` ou `Math.random`. Les fake timers Vitest servent aux timers JavaScript ; ils ne font pas avancer magiquement la physique ou l'horloge interne Phaser.

Après usage de `vi.useFakeTimers`, nettoyer les tâches selon le test et restaurer `vi.useRealTimers` dans un teardown fiable. Éviter `runAllTimers` pour une boucle infinie de jeu. Chaque test construit son propre état.

## Configuration et CI

Séparer les ensembles de tests Node, DOM et navigateur par configuration/projets lorsque cela est nécessaire. Vérifier la syntaxe de la version Vitest installée ; les exemples d'anciens workspaces peuvent être périmés. Les globs ne doivent pas faire exécuter des E2E par Vitest par accident.

En CI, utiliser `vitest run`, jamais le mode watch. Une couverture demandée doit viser les règles et transitions critiques, avec le provider compatible ; ne pas compter fichiers générés et assets. Garder un échec de typecheck distinct d'un échec de test ou de build.

Sources : [environnements](https://vitest.dev/guide/environment), [Browser Mode](https://vitest.dev/guide/browser/), [timers](https://vitest.dev/guide/mocking/timers).
