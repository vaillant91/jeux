# Mise à jour sans interrompre une partie

## Stratégie par défaut

Pour un petit jeu, utiliser `generateSW` et `registerType: 'prompt'`. L'application enregistre le worker une seule fois, par exemple via le module virtuel `virtual:pwa-register` suivant la version installée. Ne pas cumuler un enregistrement manuel et un autre injecté sans comprendre leur interaction.

Traiter trois états différents : cache prêt pour offline, nouvelle version disponible et erreur d'enregistrement. Un échec de service worker doit laisser la version en ligne jouable. Le message « prêt hors ligne » ne doit pas apparaître avant que les ressources nécessaires soient disponibles.

Quand une version attend : afficher une proposition accessible. Le joueur peut différer ; conserver le worker en attente pendant une partie. À l'acceptation et au point sûr, sauvegarder les données nécessaires, puis appeler le mécanisme de mise à jour documenté par la version du plugin. Désactiver les actions concurrentes et éviter les boucles de reload.

Ne pas activer `skipWaiting`, `clientsClaim` et le rechargement automatique à l'aveugle : leur interaction peut remplacer le runtime pendant une partie. `autoUpdate` est envisageable seulement si les exigences du produit acceptent le comportement et que la reprise est testée.

## Cohérence de version

Les bundles et assets doivent correspondre au code en exécution. Préférer les imports fingerprintés pour les ressources liées à une version. Tester les imports différés d'un ancien onglet après activation de B : un nettoyage de cache peut supprimer les chunks dont A a encore besoin.

Ne pas supprimer toutes les caches du même origin. Utiliser les mécanismes du plugin/Workbox, inspecter leur isolation par scope et nom si plusieurs jeux cohabitent. Ne pas modifier les caches Workbox à la main sans besoin démontré et scénario de migration.

Le schéma de sauvegarde évolue indépendamment du cache. Une mise à jour doit migrer les versions connues et préserver des données non comprises ; éviter que le retour à un ancien build efface une sauvegarde récente.

## Worker personnalisé

Choisir `injectManifest` si une exigence concrète dépasse `generateSW`. Dans ce cas, vérifier le point d'injection du precache, le routing, les messages d'activation, les erreurs, les exclusions et la recette A/B. Ne pas créer un worker maison pour quelques fichiers statiques.

## Diagnostic

Observer registration, scope, installing/waiting/active, controller de la page, contenu du precache et réponses réseau. Ne pas commencer par « vider tous les caches » : cela masque souvent le problème que rencontreront les utilisateurs.

Sur Pages, les en-têtes HTTP ne se configurent pas comme sur un serveur personnel. Vérifier les headers servis ; ne pas ajouter un fichier de configuration NGINX ou Netlify en prétendant qu'il contrôle GitHub Pages.

Sources : [confirmation de mise à jour](https://vite-pwa-org.netlify.app/guide/prompt-for-update.html), [enregistrement](https://vite-pwa-org.netlify.app/guide/register-service-worker.html), [worker personnalisé](https://vite-pwa-org.netlify.app/guide/inject-manifest).
