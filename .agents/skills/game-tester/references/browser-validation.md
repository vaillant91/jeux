# Recette navigateur et diagnostic

## Parcours minimal du jeu

1. Ouvrir une session propre ; capturer erreurs JS, console et requêtes en échec. Attendre un état prêt explicite plutôt qu'un sommeil fixe.
2. Démarrer, effectuer l'action principale, atteindre victoire ou défaite, puis rejouer. Vérifier feedback, score et boutons.
3. Répéter quitter/rejouer plusieurs fois ; rechercher handlers, musiques ou objets dupliqués. Tester pause, perte de focus, retour d'arrière-plan et relâchement des contrôles.
4. Tester le viewport mobile cible, le tactile, l'orientation/resize et le clavier des menus. L'émulation n'est pas une mesure de performance d'un vrai téléphone.
5. Recharger, vérifier réglages et sauvegarde, puis tester une sauvegarde invalide dans un contexte isolé.
6. Exécuter sur le build de production si imports, assets, PWA ou configuration ont changé.

Pour automatiser un canvas, utiliser ses dimensions réelles et transformer les coordonnées logiques en coordonnées écran. Préférer des actions utilisateur et des résultats visibles. Si nécessaire, exposer une interface de test minimale activée uniquement en développement/test : état sérialisable en lecture, seed et déclencheurs bornés. Vérifier son absence du bundle public ; ne pas expédier une console de triche permanente.

## PWA : recette de deux versions

Préparer A puis B depuis des sources distinctes identifiables, au même origin et au même chemin, avec un même profil navigateur. Une simple modification de `dev` n'est pas cette recette.

- A : charger en ligne, attendre service worker activé **et page contrôlée** (recharger si nécessaire), puis vérifier que le contenu requis est effectivement en cache.
- Couper le réseau, recharger et jouer une partie entière ; visiter aussi un niveau chargé tardivement. Différencier les contenus garantis offline des téléchargements optionnels.
- Revenir en ligne, servir B sans changer l'origin ; déclencher la vérification de mise à jour et observer le worker en attente et la proposition utilisateur.
- Refuser/différer pendant une partie : aucune perte d'état ni recharge intempestive.
- Accepter au point sûr : sauvegarder ce qui doit l'être, activer/recharger une seule fois, constater B et les données attendues.
- Si plusieurs onglets sont supportés, vérifier le comportement de l'ancien onglet lors de l'activation. Inspecter le cache des anciens bundles et les imports différés ; ne pas supposer qu'ils restent disponibles.

Faire ces essais avec un profil dédié, sans supprimer toutes les données d'autres applications sur le même origin. GitHub Pages partage l'origin entre plusieurs dépôts : cette contrainte fait partie du diagnostic.

## Distinguer les causes

| Symptôme | Vérifications prioritaires |
| --- | --- |
| Écran noir | Exception initiale, contexte WebGL, dimensions canvas, scène active, chargement |
| Fonctionne en dev, échoue sur Pages | `base`, casse des fichiers, imports, assets secondaires, réponses HTML à la place de JS |
| Double score au restart | Abonnements externes et événements collision répétés |
| Offline incomplet | Entrées précachées, taille limite, assets imbriqués, fonts/audio externes |
| Ancienne version persistante | Lifecycle SW, scope, cache HTTP, worker en attente, onglets ouverts |
| Contrôle bloqué | Blur, pointercancel, remise à zéro du mapping d'input |

Comparer avant/après avec la même seed et le même scénario. Des screenshots sont utiles pour la lisibilité ou une régression visuelle, pas comme seule assertion de fonctionnement. Les différences de GPU, police et antialiasing demandent une tolérance raisonnée.
