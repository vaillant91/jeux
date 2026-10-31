---
name: game-architect
description: Concevoir et structurer un petit jeu navigateur TypeScript et Phaser 4, cadrer sa boucle jouable, séparer règles et moteur, organiser états et sauvegardes. À utiliser pour un nouveau jeu, une nouvelle mécanique structurante ou une refonte, pas pour imposer une refonte à chaque correction locale.
---

# Architecture de petits jeux

Transformer la demande en une tranche jouable et testable, avec le moins de structure nécessaire. Respecter le genre et l'ambition demandés ; ne pas concevoir une plateforme de jeux à la place d'un jeu.

## Procédure

1. Inspecter le projet, ses conventions, ses versions et ses tests. Sur un dépôt vide, consulter [bootstrap.md](references/bootstrap.md) pour établir la toolchain et les commandes.
2. Définir en quelques lignes la boucle : action du joueur, retour perceptible, progression, fin de partie et rejouabilité. Fixer les contrôles clavier/tactile, l'orientation et les critères d'acceptation. Faire des hypothèses explicites si ces choix sont réversibles.
3. Choisir la plus petite tranche verticale qui prouve cette boucle. Séparer le nécessaire des améliorations futures ; ne pas bloquer un prototype derrière une spécification exhaustive.
4. Utiliser [boundaries.md](references/boundaries.md) pour la structure, les contrats de temps/aléatoire, la physique et les données persistantes. Créer seulement les dossiers qui reçoivent du code.
5. Implémenter ou guider l'implémentation jusqu'à une tranche fonctionnelle. Écrire une courte décision seulement pour un choix difficile à inverser ou non évident ; pas d'ADR pour chaque fichier.
6. Vérifier les critères de gameplay, les dépendances entre couches et le chemin vers un build testable. Réviser la conception si elle rend les tests artificiels ou le jeu inutilement complexe.

## Contraintes utiles

- Les règles testables ne dépendent pas des objets Phaser, du DOM, du stockage global ou d'un singleton de jeu. Ne pas dupliquer pour autant toute la physique du moteur dans un second monde métier.
- Un état a un propriétaire. Les scènes présentent et orchestrent ; elles ne servent pas simultanément de base de données, de système de sauvegarde et de moteur de règles.
- Privilégier fonctions, types et composition. Ajouter un bus d'événements, une machine à états générique ou une injection de dépendances seulement quand plusieurs usages en ont besoin.
- Une configuration d'équilibrage expose des unités et des bornes. Éviter les nombres cachés dans plusieurs scènes et l'optimisation sans profilage.
- Concevoir les menus et réglages pour être utilisables au clavier et lisibles sur mobile ; du DOM peut compléter le canvas sans imposer un framework UI.

## Résultat attendu

Une structure adaptée au jeu, des règles explicites, une boucle jouable et des critères vérifiables. Pour une demande d'architecture seule, livrer un plan concret avec responsabilités et compromis, sans effectuer une refonte non demandée.
