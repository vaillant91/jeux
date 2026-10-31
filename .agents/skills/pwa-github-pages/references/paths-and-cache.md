# Chemins, manifest et contrat offline

## Une seule base de déploiement

| Destination | `base` attendu |
| --- | --- |
| `https://compte.github.io/jeu/` | `/jeu/` |
| `https://compte.github.io/` | `/` |
| Domaine personnalisé servant le jeu à la racine | `/` |

Normaliser en chemin absolu avec slash initial et final. Éviter `./` comme remède universel aux problèmes Pages. Conserver une configuration explicite pour un domaine ou un chemin différent. Une variable de build `PAGES_BASE_PATH` peut porter cette valeur ; elle doit être validée avant le build CI et lue par la configuration Vite.

Pour les URLs chargées en code, importer les assets via Vite ou utiliser `import.meta.env.BASE_URL`. Ce dernier est remplacé à la compilation : une concaténation dynamique arbitraire avec un chemin racine ne sera pas réparée par Vite. Vérifier la casse exacte des noms de fichiers, souvent masquée sur Windows mais pas sur Pages.

GitHub Pages ne fournit pas une réécriture SPA générale. Pour un petit jeu, préférer une URL d'entrée unique et des états internes ; si le produit demande des routes, choisir hash routing ou une stratégie explicite testée en accès direct. Ne pas considérer un `404.html` improvisé comme un serveur de routage.

## Manifest et enregistrement

Vérifier dans les fichiers générés et dans le navigateur : `id` stable, `name`, `short_name`, `start_url`, `scope`, `display`, couleurs et icônes. Choisir une identité distincte pour chaque jeu sur le même origin, et stable entre releases. Utiliser des URLs résolues qui restent sous la base ; ne pas changer `id` à chaque build.

Prévoir de vraies icônes PNG notamment 192×192 et 512×512, plus une icône maskable conçue avec zone sûre si déclarée. Ne pas simplement déclarer `purpose: maskable` sur un dessin rogné. Vérifier dimensions, chargement et apparence ; le texte `sizes` du manifest n'est pas une vérification du fichier.

Le scope du manifest organise la navigation installée ; le scope du service worker définit les pages contrôlées. Vérifier les deux indépendamment. Le worker d'un dépôt doit être servi sous sa base et contrôler ce dépôt, pas les jeux voisins. Tester le comportement installé sur les plateformes visées ; la présence d'un bouton d'installation dépend du navigateur et ne doit pas bloquer le jeu.

## Contenu offline

Définir explicitement ce qui doit fonctionner sans réseau après une première visite complète : shell, moteur, sprites, atlas et images associés, niveaux initiaux, sons et polices. Les gros contenus optionnels peuvent rester téléchargeables avec une UI de disponibilité.

Inspecter le precache produit : les defaults ne garantissent pas l'inclusion de tous les sons, JSON et assets de jeu. Configurer `includeAssets` pour les ressources statiques appropriées et/ou `workbox.globPatterns` selon les sorties. Vérifier les limites `maximumFileSizeToCacheInBytes` et les messages de build. Compresser ou segmenter avant de relever largement une limite.

Préférer des assets locaux ou bundlés pour le noyau offline. Pour du runtime caching, limiter les motifs d'URL, la stratégie, la taille et la durée selon le contenu ; traiter réponses opaques et CORS explicitement. Ne pas cacher aveuglément toutes les requêtes ni des erreurs 404. Le cache est évictable par le navigateur : une installation ne garantit pas une conservation permanente.

Un fallback de navigation doit viser l'entrée sous la base et ne pas transformer une requête JS/texture manquante en HTML. Vérifier statut, type MIME et contenu des réponses, pas seulement un HTTP 200.

Sources : [Vite Pages](https://vite.dev/guide/static-deploy#github-pages), [assets PWA](https://vite-pwa-org.netlify.app/guide/static-assets.html), [precache](https://vite-pwa-org.netlify.app/guide/service-worker-precache.html).
