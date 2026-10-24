# Cycle de vie et exécution

## Scènes et ressources

- Le constructeur définit l'identité de la scène ; `init` remet l'état de session à zéro, `preload` prépare les ressources, `create` construit les objets et les abonnements de l'exécution courante. Vérifier ce qui doit être recréé après restart.
- Distinguer pause/resume, sleep/wake, shutdown/restart et destruction définitive. Une scène arrêtée peut être relancée : un nettoyage uniquement sur destruction laisse fuiter les ressources entre parties.
- Nettoyer les listeners DOM/window, bus partagés, abonnements au jeu, fetch annulables et ressources externes sur shutdown ; conserver les références des callbacks pour retirer seulement ceux de cette scène.
- Phaser gère une partie de ses ressources de scène. Inspecter leur propriété avant de détruire textures, sons ou animations partagés avec d'autres scènes. Ne pas faire de `removeAllListeners` sur un émetteur global.
- Les callbacks asynchrones doivent ignorer une ancienne exécution de scène (annulation ou identifiant de génération). Ne pas créer un objet dans une scène qui a été arrêtée pendant le chargement.
- Après cinq cycles jouer/quitter/rejouer, un clic doit produire une seule action et une collision une seule récompense. Vérifier aussi l'absence de musique dupliquée et de canvas supplémentaires.

## Temps et physique

- Documenter les unités. Le delta de `update` Phaser est en millisecondes ; convertir explicitement en secondes pour une intégration métier qui attend des secondes.
- Un déplacement manuel indépendant du framerate utilise vitesse × delta. Les vélocités du moteur physique sont déjà intégrées par lui ; ne pas appliquer cette formule une deuxième fois.
- Utiliser les timers de scène pour des événements qui suivent la pause de la scène, une horloge injectée pour les règles testables et le temps mur pour des échéances réelles explicitement demandées.
- En retour d'arrière-plan, éviter un grand saut de simulation. Définir pause automatique, reprise et remise à zéro des touches maintenues ; borner le rattrapage si le jeu utilise un accumulateur.
- Choisir sans physique pour un puzzle discret, Arcade pour des collisions simples, Matter quand contraintes ou polygones le demandent. Ne pas mélanger les deux pour le même corps.
- Collision : gérer l'idempotence d'un événement fatal, les overlaps continus, les corps désactivés et le passage à grande vitesse. Vérifier l'ordre mise à jour/contacts avant d'ajouter un contournement.
- Avec pooling, réinitialiser état métier, vélocité, corps actif, collisions, visibilité, animation et abonnements. Introduire un pool après mesure ou pour un volume clairement répétitif.

## Contrôles

- Mapper clavier, pointeur et tactile vers des actions du jeu. Distinguer appui unique, maintien et relâchement ; le rendu ne doit pas décider seul des règles.
- Tester coordonnées monde/caméra après scaling ou déplacement de caméra. Prévoir multitouch si déplacement et action doivent être simultanés.
- Gérer perte de focus et annulation de pointeur pour éviter une direction bloquée. Ne pas neutraliser tout le clavier de la page quand un menu ou champ DOM a le focus.
- Limiter `touch-action` et la prévention du scroll à la surface qui en a besoin. Préserver le zoom et la navigation dans les autres parties de l'interface.

## Audio et assets

- Débloquer l'audio sur un geste utilisateur ; garder le jeu fonctionnel si la lecture est refusée. Prévoir mute persistant et réglages cohérents avec pause/visibilité.
- Afficher le chargement et traiter les erreurs avec un message exploitable ou un fallback. Le succès HTML ne garantit pas celui d'une texture ou d'un atlas.
- Pour un fichier importé par Vite : importer son URL, éventuellement avec `?url`, puis la fournir au loader. Pour `public/assets/foo.png`, utiliser une construction centralisée telle que `${import.meta.env.BASE_URL}assets/foo.png`.
- Les JSON d'atlas, tilemaps et feuilles de sprites peuvent référencer d'autres fichiers : vérifier leur résolution réelle et inclure ces dépendances dans les tests de production et le cache offline.
- Éviter collisions de clés de textures/animations et rechargements inutiles au restart. Nommer et documenter les assets ainsi que leur provenance/licence ; ne pas prétendre qu'un fichier trouvé en ligne est libre.
