# Cosmo Dash

Un petit jeu d’arcade spatial fait pour découvrir la création de jeux avec **TypeScript, Phaser 4 et Vite**. La mission : ramasser 8 étoiles en 45 secondes, tout en évitant les astéroïdes. Une partie se joue au clavier (flèches ou ZQSD) ou avec les boutons tactiles.

## Jouer en local

Prérequis : Node.js 22 LTS (ou une version récente compatible avec Vite) et npm.

Depuis ce dossier (`defi`) :

```bash
npm install
npm run dev
```

Vite affiche l’adresse locale à ouvrir, en général <http://localhost:5173>. Les modifications de code sont rechargées automatiquement.

Pour générer puis inspecter la version de production :

```bash
npm run build
npm run preview
```

Les fichiers optimisés sont créés dans `dist/`. La PWA et son cache hors ligne sont générés pendant le build. Pour vérifier le mode PWA localement, lance `npm run build`, puis `npm run preview` et ouvre l’adresse indiquée. Il faut visiter le site une première fois en ligne pour installer le service worker ; après son activation, les fichiers du jeu restent disponibles hors connexion. Le navigateur doit servir le jeu en HTTPS ou depuis `localhost` pour autoriser l’installation PWA.

## Tests

```bash
npm test
npm run test:watch
```

Les règles indépendantes de Phaser sont testées avec Vitest.

## Déploiement GitHub Pages

Le workflow [`../.github/workflows/deploy-defi.yml`](../.github/workflows/deploy-defi.yml) installe les dépendances, construit le site, puis publie `dist/` sur GitHub Pages à chaque push sur `main` qui modifie `defi/`. Il est aussi lançable manuellement depuis l’onglet **Actions**.

Dans les paramètres du dépôt GitHub, ouvrir **Settings → Pages**, puis sélectionner **GitHub Actions** comme source de déploiement. Pour ce dépôt, l’adresse attendue est <https://vaillant91.github.io/jeux/>. La base Vite `/jeux/` n’est activée que dans GitHub Actions ; en local, le jeu reste servi à la racine.

## Organisation

- `src/main.ts` : scène Phaser, commandes, score, chrono et collisions.
- `src/game/rules.ts` : règles réutilisables et indépendantes du moteur.
- `src/style.css` : interface adaptative PC/tablette/mobile.
- `vite.config.ts` : build Vite et génération du manifeste/service worker par `vite-plugin-pwa`.
- `public/` : icônes du jeu et de la PWA.

Le jeu ne possède pas de backend et ne charge aucun contenu de jeu depuis un service externe. Le rendu et les contrôles fonctionnent entièrement dans le navigateur.
