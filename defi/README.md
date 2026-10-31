# Défi ton pote

Portage de `../defi_ton_pote.py` en TypeScript strict, Phaser **4.2.1**, Vite, Vitest et vite-plugin-pwa. La campagne et la carte de démonstration reproduisent les données Python à l’identique. L’arcade conserve ses codes et son générateur CPython. L’éditeur importe P1/P2/P3/P4 et exporte P4.

- Arcade : survivre 45 secondes, collecter des fragments, esquiver et battre son record.
- Parcours : 12 niveaux, trois vies, checkpoints, gemmes, cœurs, ressorts et monstres patrouilleurs.
- Atelier : cartes 40 × 11, quatre biomes, peinture, gomme, annulation/rétablissement, bibliothèque locale, test et partage.
- Clavier : flèches, ZQSD ou WASD ; Espace pour sauter/esquiver ; Maj pour courir ; P/Échap pour mettre en pause. Les boutons tactiles offrent les mêmes actions. La perte de focus met la partie en pause.

## Démarrer

Depuis ce dossier, avec Node indiqué dans `.nvmrc` :

```powershell
npm ci
npm run dev
```

## Vérifier

```powershell
npm run typecheck
npm run test:run
$env:PAGES_BASE_PATH='/jeux/'
npm run build
npm run preview -- --host 127.0.0.1 --port 4174 --strictPort
```

Dans un autre terminal, avec Chrome installé :

```powershell
npm run test:browser
npm run test:update
```

Le runner utilise Playwright avec le navigateur Chrome local par défaut. Pour utiliser Chromium fourni par Playwright : `npx playwright install chromium`, puis définir `BROWSER_CHANNEL=chromium`. `TEST_BASE_URL` permet de changer `http://127.0.0.1:4174/jeux/`. Le test de mise à jour recompilé attend aussi un serveur preview sur cette base ; il modifie temporairement le titre HTML puis restaure source et build dans un bloc `finally`. Ne pas modifier `index.html` simultanément à ce test. Les captures vont dans `test-results/` (ignoré par Git).

Les tests unitaires couvrent parité Python, formats de codes, génération, validation, physique, fin de partie, score, aléatoire et stockage. Les fixtures peuvent être régénérées avec `python scripts/python-fixtures.py`, sans installation de Pygame. Les icônes PNG sont générables par `python scripts/icons.py` sans bibliothèque tierce.

## PWA et GitHub Pages

Le chemin Pages existant est `/jeux/`. La configuration `PAGES_BASE_PATH` accepte `/` ou un chemin absolu terminé par `/`. En développement le défaut est `/`. Pour le dépôt actuel, le workflow `.github/workflows/deploy-defi.yml` utilise `/jeux/`, remplaçable par une variable GitHub du même nom.

Le manifest et le service worker partagent cette base. Tous les éléments nécessaires aux parties et à l’éditeur sont précachés. Le bouton de mise à jour demande de quitter la partie avant activation ; une partie n’est pas rechargée automatiquement. Le stockage et les caches du navigateur peuvent être effacés par l’utilisateur ou le système : exporter les codes importants.

Le workflow valide les PR sans publier. Un push sur `main` ou un lancement manuel sur `main` valide puis déploie le même artefact avec GitHub Pages. Régler **Settings → Pages → Source → GitHub Actions** dans le dépôt. Le workflow est préparé ; aucun déploiement n’est annoncé sans exécution réussie.

## Sources et limites

- `src/game/levels.ts` : génération, validation, édition.
- `src/game/codec.ts` : protocole zlib/base64 P1–P4 borné.
- `src/game/random.ts` : MT19937 compatible CPython, codes et défi quotidien.
- `src/game/platform.ts` et `arcade.ts` : simulations indépendantes du moteur.
- `src/main.ts` : rendu Phaser, menus DOM, entrées, navigation et enregistrement PWA.
- `src/storage.ts` : bibliothèque/records versionnés et gestion des erreurs.
- [Analyse détaillée du Python](docs/PYTHON_ANALYSIS.md).
- [Résultats et limites de validation](docs/VALIDATION.md).

Les visuels sont redessinés dans Phaser. Le jeu externe `cache_cache_3d.py`, lancé par le menu Python, n’est pas inclus. Les variantes de monstres seulement esquissées dans le Python ne sont pas présentées comme jouables. Le pas fixe et les positions flottantes améliorent l’indépendance à la fréquence d’affichage ; le rendu et les trajectoires ne sont pas garantis identiques à Pygame frame par frame.
