# Initialiser la stack sans figer des versions périmées

Lire ce document pour un nouveau projet ou une réparation de toolchain. Une modification de gameplay n'appelle pas une mise à jour générale des dépendances.

## Résoudre les versions

1. Lire `package.json`, le lockfile, la version Node, les fichiers de configuration et les contraintes CI existants.
2. Pour un projet neuf, vérifier les versions publiées de `phaser`, `vite`, `vitest`, `typescript`, `vite-plugin-pwa`, leurs `engines` et `peerDependencies` via le registre et les documentations officielles. Par exemple `npm view vite version engines` et `npm view vite-plugin-pwa peerDependencies engines`. Résoudre ensuite une combinaison compatible, pas simplement une collection de tags `latest`.
3. Exiger Phaser de major 4 pour cette stack. Si indisponible dans l'environnement, signaler le blocage ; ne pas substituer Phaser 3 ni une préversion sans l'expliquer.
4. Choisir une version Node LTS encore supportée et compatible avec tous les outils ; la consigner dans `.nvmrc` ou `.node-version` et la reprendre en CI. Sur Windows, utiliser le gestionnaire installé plutôt qu'imposer un script Unix.
5. Phaser fournit ses types : ne pas ajouter un ancien paquet `@types/phaser`. Installer Phaser en dépendance de production, les outils en dépendances de développement. Verrouiller les résolutions par le lockfile ; `npm ci` sert ensuite aux installations reproductibles.

## Socle minimal

- `index.html`, `src/main.ts`, un conteneur de jeu et une feuille de style responsive.
- `vite.config.ts`, configuration TypeScript de l'application et des outils si nécessaire, configuration Vitest isolant les tests purs.
- TypeScript : `strict`, `noEmit`, résolution adaptée au bundler et bibliothèques DOM côté application. Activer `noUncheckedIndexedAccess` sur un projet neuf ; traiter les éléments absents au lieu de multiplier les assertions non nulles. Ne pas assouplir les types pour cacher une API incompatible.
- Types Vite via `vite/client`. Si le module virtuel de PWA est importé, ajouter aussi `vite-plugin-pwa/client` suivant la version installée.
- Ignorer `node_modules/`, `dist/`, `coverage/` et les rapports de test temporaires. Versionner les sources, les assets distribuables et le lockfile.

Contrat conseillé, à adapter à la configuration TypeScript réellement créée :

| Script | Comportement |
| --- | --- |
| `dev` | `vite` |
| `typecheck` | Contrôle de tous les projets TS concernés, p. ex. `tsc --noEmit` pour une configuration unique |
| `test` | `vitest` en mode interactif |
| `test:run` | `vitest run`, non interactif, échoue si les tests échouent |
| `build` | `vite build` ; le pipeline exécute séparément le typecheck |
| `preview` | `vite preview`, vérification locale du build |
| `check` | Typecheck, tests non interactifs, puis build |

Ne pas ajouter `--passWithNoTests` pour verdir un projet dépourvu de tests métier. Ajouter lint/format si présent ou utile au projet, sans installer une suite d'outils uniquement pour une convention.

## Première tranche

Faire démarrer une scène simple puis une action jouable, une condition de fin et un redémarrage. Ajouter les premières règles testées avant de développer des menus complexes. Configurer ensuite l'enveloppe PWA et valider la production sous un sous-chemin dès le début, avant de multiplier les assets.

Documenter dans le README du jeu : commandes, version Node, contrôles, emplacement des réglages, test local PWA et URL de déploiement lorsqu'elle est connue.

Sources à consulter pour les versions effectivement retenues : [Vite](https://vite.dev/guide/), [Vitest](https://vitest.dev/guide/), [Phaser](https://github.com/phaserjs/phaser/releases), [Vite PWA](https://vite-pwa-org.netlify.app/guide/).
