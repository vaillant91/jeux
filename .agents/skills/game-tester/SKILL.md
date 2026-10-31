---
name: game-tester
description: Tester et déboguer un jeu TypeScript Phaser 4 avec Vitest et des vérifications dans un vrai navigateur. À utiliser pour un bug, des régressions, des règles de jeu, le cycle de vie des scènes ou une validation de jouabilité ; différencie tests Node, DOM et moteur réel.
---

# Tests et diagnostic des jeux

Choisir la preuve qui correspond au risque. Un test de fonction n'établit pas qu'un sprite est visible ; une capture n'établit pas qu'un restart nettoie les événements.

## Workflow

1. Reproduire le problème ou définir le comportement attendu. Relever version, seed éventuelle, étapes, erreurs console/réseau, viewport et fréquence du problème. Pour un bug, conserver une observation avant correction.
2. Choisir le niveau le plus bas capable de détecter le défaut avec [test-strategy.md](references/test-strategy.md). Éviter de mocker le moteur entier pour obtenir des tests verts.
3. Écrire une régression significative lorsque le comportement s'y prête, appliquer une correction ciblée, vérifier qu'elle échoue sur l'ancien comportement puis passe avec la correction quand c'est praticable.
4. Pour le moteur, l'input, les assets, le rendu et le cycle de vie, suivre [browser-validation.md](references/browser-validation.md). Utiliser les outils navigateur disponibles ; ajouter un runner seulement si son bénéfice justifie sa maintenance.
5. Exécuter les tests concernés, le typecheck et le build ; élargir aux contrôles transverses si des interfaces partagées changent. Réparer la cause des échecs, pas les assertions pour qu'elles acceptent le bug.
6. Rendre un résultat reproductible : commandes, scénario, attentes/résultats, défauts restants et contrôles non exécutés.

## Discipline

- Ne pas activer systématiquement couverture à 100 %, snapshots de scènes ou tests de getters triviaux. Couvrir transitions et invariants à risque.
- Pas de temporisation arbitraire pour rendre une suite stable : attendre un état observable, borner le timeout et diagnostiquer un flake au lieu de le masquer par des retries.
- Restaurer mocks, timers, listeners, stockage et instances du moteur après chaque test qui les modifie.
- Ne pas vider le service worker pour faire disparaître un défaut de mise à jour avant d'avoir reproduit et documenté ce défaut.
- Si aucun navigateur n'est disponible, terminer les vérifications statiques et unitaires possibles, puis fournir le scénario restant. Ne pas déclarer la recette navigateur réussie.
