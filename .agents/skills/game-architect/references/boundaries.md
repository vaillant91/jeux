# Frontières, état et données

## Structure indicative

```text
src/
  main.ts                 composition, création et destruction du jeu
  game/
    config.ts             configuration Phaser et dimensions logiques
    scenes/               cycle de vie, orchestration, présentation
    objects/              objets visuels réutilisés si nécessaire
  domain/                 règles, transitions, score, progression
  platform/               stockage, audio global, cycle de vie navigateur
  ui/                     menus DOM, réglages, messages PWA accessibles
  pwa/                    enregistrement et expérience de mise à jour
  assets/                 imports traités par Vite
public/
  assets/                 fichiers chargés par URL, si nécessaire
  icons/                  icônes installables
tests/                    tests transverses ; tests unitaires colocalisés possibles
.github/workflows/        vérifications et déploiement
```

Ce n'est pas une liste de dossiers obligatoires. Trois fichiers bien séparés peuvent suffire à un prototype. Regrouper par fonctionnalité si le jeu existant le fait déjà.

## Dépendances et simulation

`domain` ne doit pas importer `game`, Phaser ou `platform`. La racine compose les adaptateurs et les scènes. Un type de domaine expose des valeurs, pas un `Sprite`, une `Scene` ou un `Storage` global.

Pour une règle qui utilise le temps ou le hasard, injecter la donnée nécessaire : `step(state, input, dtSeconds, random)` est un exemple, pas une signature obligatoire. Consigner les unités. Injecter un générateur reproductible si les niveaux, les tests ou les replays en dépendent ; conserver seed et séquence d'entrées pour reproduire un bug.

Ne pas promettre un replay parfaitement déterministe de la physique Phaser entre plateformes. Pour un puzzle, tester une grille et ses transitions directement. Pour un jeu d'action avec Arcade/Matter, laisser le moteur résoudre les contacts, convertir les événements utiles en décisions métier et tester ces décisions séparément. Si une simulation à pas fixe est nécessaire, borner le rattrapage après suspension ; ne pas avancer le moteur physique une deuxième fois par erreur.

## États

Définir les transitions pertinentes : menu, partie active, pause, résultat. Une union discriminée ou une petite table suffit souvent. Exclure les transitions invalides : score après défaite, double récompense pour le même événement, reprise d'une partie détruite.

Séparer durée de partie et horloge murale. La pause doit geler les règles concernées ; le menu reste utilisable. Définir ce qui est conservé au restart, au changement de niveau et au retour au menu. Éviter le mélange entre score courant, record et progression persistée.

## Sauvegarde locale

- Persister des données sérialisables, versionnées et propres au jeu (`game-id:save`), jamais un graphe d'objets Phaser.
- Lire le JSON comme `unknown`, valider formes et bornes, migrer les versions connues ; traiter un fichier corrompu sans bloquer le démarrage.
- Préserver une sauvegarde d'une version future non reconnue plutôt que l'écraser automatiquement.
- Encapsuler les erreurs de quota et d'accès ; garder le jeu jouable si le stockage est indisponible. Utiliser IndexedDB seulement si le volume ou l'asynchronisme le justifie.
- Écrire aux points utiles (fin de partie, réglages), pas à chaque frame. Les actions explicites sont plus fiables qu'une sauvegarde uniquement dans `beforeunload` sur mobile.
- Les records locaux ne sont pas fiables pour un classement compétitif. Ne pas inventer un backend sécurisé sur GitHub Pages.

## Critères de conception

Écrire des critères observables, par exemple : une collision létale produit une seule défaite ; rejouer remet le score à zéro et garde le record ; mettre en pause n'avance pas le compte à rebours ; refuser une mise à jour conserve la partie.

Pour l'équilibrage, exposer vitesse, durée, seuils et progression dans une configuration typée. Ne pas transformer un objectif vague de plaisir en une métrique artificielle : jouer la tranche et ajuster sur observation.
