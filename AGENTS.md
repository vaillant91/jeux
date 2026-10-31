# Jeux navigateur TypeScript / Phaser 4

## Périmètre

Ce dépôt contient des skills réutilisables pour créer de petits jeux PWA. Ne pas générer un jeu ou installer sa toolchain à l'occasion d'une simple modification des skills. Dans un dépôt de jeu qui reprend ce fichier, appliquer les conventions ci-dessous en les adaptant au code existant.

## Façon de travailler

- Communiquer en français ; garder les identifiants et noms de fichiers en anglais.
- Lire les instructions locales, l'état Git, les scripts et le lockfile avant de modifier le projet. Préserver les changements utilisateur.
- Pour une demande de jeu peu détaillée, choisir des hypothèses réversibles et livrer une première boucle jouable : démarrer, jouer, terminer, rejouer. Poser une question seulement si une ambiguïté bloque réellement la réalisation.
- Avancer par tranches jouables ; choisir l'architecture minimale qui permet de tester les règles. Ne pas ajouter ECS, backend, framework UI ou monorepo sans besoin concret.
- Utiliser TypeScript strict, Phaser **4**, Vite, Vitest et vite-plugin-pwa. Conserver le gestionnaire de paquets existant ; pour un nouveau projet, npm et un lockfile versionné.
- Vérifier les versions installées et leurs API. Ne pas convertir silencieusement une demande Phaser 4 en Phaser 3, ni copier une API de rendu Phaser 3 sans vérification.
- Implémenter, vérifier, corriger les échecs pertinents puis livrer. Ne pas demander validation de chaque choix technique réversible. Les skills ne donnent pas d'autorisation de publication, de push ou de modification de compte ; suivre la demande utilisateur et les permissions de l'environnement.

## Routage des skills

Lire le `SKILL.md` concerné dans `.agents/skills/`, puis uniquement les références utiles. Plusieurs skills peuvent contribuer à une tâche ; ils ne supposent ni quatre agents ni une délégation automatique.

| Situation | Skill |
| --- | --- |
| Nouveau jeu, cadrage des règles, structure, refonte, sauvegardes | `game-architect` |
| Scènes, contrôles, physique, rendu, audio, game feel, performance | `phaser-developer` |
| Bug, régression, tests Vitest, vérification navigateur | `game-tester` |
| Manifest, offline, mise à jour, build, chemins, CI, Pages | `pwa-github-pages` |

Pour un nouveau jeu complet : cadrer brièvement avec `game-architect`, implémenter avec `phaser-developer`, vérifier avec `game-tester`, puis préparer la livraison avec `pwa-github-pages`. Pour une petite correction, charger uniquement ce qui sert à la correction.

## Contrat de livraison d'un jeu

- Typecheck, tests pertinents et build de production réussis. Vite ne remplace pas le contrôle des types.
- Parcours jouable contrôlé dans un vrai navigateur lorsque disponible : entrée, fin, reprise et redémarrage ; contrôles tactiles pour une cible mobile.
- Si PWA touchée : vérifier le build servi au vrai sous-chemin, son service worker, son fonctionnement offline après installation du cache et son scénario de mise à jour.
- Ne pas confondre tests Node, simulation DOM, navigateur automatisé et appareil réel. Déclarer les contrôles non exécutés et leur raison.
- Rendre compte du résultat, des commandes réellement passées, des limites restantes et de l'emplacement des fichiers. Ne jamais annoncer une publication sans preuve du déploiement.
