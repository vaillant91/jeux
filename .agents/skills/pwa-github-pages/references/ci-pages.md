# CI reproductible et publication Pages

## Préparation

Lire les workflows existants avant de créer des doublons. Conserver le gestionnaire de paquets et le lockfile. Vérifier la version Node compatible et utiliser la même en local et en CI. Pour npm : `npm ci`, `npm run typecheck`, `npm run test:run`, puis `npm run build`.

Le [modèle de workflow](../assets/pages.yml) suppose npm, `.nvmrc`, ces scripts, une branche `main` et une configuration Vite qui lit `process.env.PAGES_BASE_PATH`. Adapter ces hypothèses au dépôt. Les actions y sont épinglées sur des SHA documentés par Vite lors de la création du pack ; vérifier les versions officielles et la compatibilité des runners avant réutilisation ou mise à jour.

Configurer la variable de dépôt `PAGES_BASE_PATH` (`/jeu/` ou `/`) et Settings → Pages → Source → GitHub Actions. La variable est une configuration publique de build, pas un secret. Si l'accès aux réglages manque, préparer les fichiers puis indiquer précisément ce réglage ; ne pas annoncer un déploiement.

Dans `vite.config.ts`, lire la variable au chargement de configuration, la valider, puis l'utiliser comme `base` et pour les URLs du manifest. Un exemple de validation est donné dans le workflow ; la configuration doit aussi rejeter les valeurs invalides en local. Un fallback `/` convient au développement, pas à une CI qui ignore sa destination.

## Propriétés du pipeline

- Sur PR : typecheck, tests et build, sans permission de publication. Ne pas utiliser `pull_request_target` pour exécuter du code non fiable avec des droits de déploiement.
- Sur push autorisé vers la branche de publication ou dispatch sur cette branche : les mêmes contrôles, puis upload de `dist`, puis déploiement avec `needs` vers le job qui a construit l'artefact.
- `contents: read` par défaut ; `pages: write` et `id-token: write` uniquement au job de déploiement ; environnement `github-pages` avec les règles de protection du dépôt.
- Réutiliser le cache du gestionnaire fondé sur le lockfile, pas un `node_modules` copié d'une autre version. Ne pas reconstruire un artefact différent après sa validation.
- Installer le navigateur et ses dépendances en CI seulement si un test navigateur configuré en a besoin. Ajouter sa commande avant l'upload, et les traces en artefacts en cas d'échec.
- Sérialiser les publications avec une concurrence dédiée. Ne pas laisser une PR annuler un déploiement de production ; distinguer leurs groupes.
- Éviter les fichiers secrets dans `dist`. Toute variable `VITE_*` utilisée côté client peut être visible publiquement.

## Vérification de l'artefact

Servir le build et ouvrir le chemin cible complet. Contrôler les URLs du HTML, JS/CSS, manifest, icônes, worker, sons et ressources chargées par JSON. La configuration `preview` est un serveur local de recette, pas un hébergement de production.

Tester offline après contrôle effectif par le worker, puis mise à jour A → B avec conservation de la partie ou reprise au point sûr. Le skill `game-tester` détaille cette recette ; si non installé, reproduire les étapes à partir des exigences de mise à jour du présent skill.

## Déploiement et récupération

L'existence du workflow n'autorise pas par elle-même un push ou une publication. Si la demande les autorise déjà, effectuer les étapes dans ce périmètre sans demander une confirmation répétée. Sinon, terminer la préparation vérifiable et expliquer l'action externe restante.

Après publication, consulter le résultat du job et l'URL fournie par `deploy-pages`. Ouvrir le jeu et contrôler les requêtes essentielles. En cas d'échec, identifier le premier job ou fichier en faute ; faire une correction causale, pas des relances identiques répétées.

Pour revenir à une version précédente, reconstruire/redéployer un commit connu et compatible avec le schéma de sauvegarde actuel, dans le périmètre autorisé. Un rollback serveur ne supprime pas instantanément les workers déjà installés : revalider la détection de mise à jour et les clients existants. Ne pas forcer un reset Git utilisateur.

Sources : [workflow Pages officiel](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [déploiement Vite](https://vite.dev/guide/static-deploy#github-pages).
