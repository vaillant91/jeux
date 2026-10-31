---
name: phaser-developer
description: Implémenter et améliorer des petits jeux TypeScript avec Phaser 4 et Vite, notamment scènes, contrôles, physique, rendu, audio, feedback et performance mobile. À utiliser pour le code du jeu et les migrations Phaser ; les tests spécialisés et la livraison PWA ont leurs propres procédures.
---

# Développement Phaser 4

Livrer une interaction jouable et lisible, pas seulement un canvas qui se charge.

## Workflow

1. Lire les scènes concernées, les règles, les assets et les versions installées. Avant une API incertaine ou une migration, consulter [phaser4-api.md](references/phaser4-api.md).
2. Identifier le critère observable : ce que le joueur fait et voit, la fin de l'action, et le comportement au redémarrage.
3. Implémenter la plus petite tranche complète. Garder les règles isolables du moteur et adapter les conventions existantes sans refonte opportuniste.
4. Appliquer [runtime.md](references/runtime.md) pour cycle de vie, temps, input, physique, audio et chargement.
5. Pour tout travail visuel, mobile ou de performance, lire [playability.md](references/playability.md). Jouer le résultat à la taille cible ; corriger les chevauchements, feedbacks manquants et contrôles imprécis.
6. Exécuter typecheck, tests pertinents et build. Vérifier dans un vrai navigateur les parcours touchés, y compris restart. Pour un bug, ajouter une régression au niveau qui peut réellement le détecter.

## Invariants

- Un seul propriétaire du `Phaser.Game`. Détruire proprement l'instance lors du démontage/HMR si le point d'entrée peut être réexécuté.
- Les ressources externes acquises par une scène ont un nettoyage à sa sortie ; le redémarrage ne doit pas multiplier les handlers.
- Ne pas multiplier par delta une vitesse déjà intégrée par la physique. Ne pas déplacer simultanément un corps dynamique par coordonnées et par vélocité sans intention explicite.
- Centraliser les URLs d'assets pour respecter le `base` Vite. Ne pas figer `/assets/...` pour un site publié sous `/nom-du-repo/`.
- Une API absente des types n'est pas réparée par `any`, `@ts-ignore` ou une assertion en chaîne. Vérifier la version, l'API et les types avant de modifier le code.

## Fin de tâche

Rapporter ce qui est jouable, les contrôles, les validations réellement exécutées et les limites observées. Une capture seule ne prouve pas les collisions, l'audio, l'offline ou les performances.
