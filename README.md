# Skills Codex — petits jeux TypeScript / Phaser 4

Pack conçu pour **TypeScript + Phaser 4 + Vite + Vitest + vite-plugin-pwa + GitHub Actions + GitHub Pages**. Les instructions sont en français, avec des identifiants de code en anglais. Documentation vérifiée le **24 octobre 2026** ; les versions exactes restent à résoudre et verrouiller dans chaque projet.

## Pourquoi quatre skills

Les quatre domaines proposés constituent un bon découpage, à condition de donner à chacun une responsabilité observable. Un cinquième « chef d'orchestre » ajouterait surtout du recouvrement : le routage commun tient dans `AGENTS.md`.

| Skill | Responsabilité | Améliorations importantes |
| --- | --- | --- |
| `game-architect` | Passer d'une idée à une boucle jouable bien structurée | Cadrage gameplay, architecture proportionnée, règles testables, sauvegardes versionnées |
| `phaser-developer` | Implémenter le jeu dans Phaser 4 | Compatibilité v4, lifecycle, input tactile, audio, rendu, lisibilité et performances |
| `game-tester` | Produire des preuves de fonctionnement et corriger les bugs | Vitest déterministe, limites du DOM simulé, vraie recette navigateur, scénario PWA A/B |
| `pwa-github-pages` | Construire et livrer une PWA fiable | Sous-chemins, cache complet, mise à jour différée, CI reproductible et Pages |

La conception du gameplay est intégrée à l'architecture ; le game feel et l'accessibilité à l'implémentation. Cela évite des skills supplémentaires chargés pour chaque petite tâche. Les détails sont dans des références lues à la demande, pas dans quatre énormes prompts systématiquement chargés.

## Arborescence

```text
AGENTS.md
README.md
.agents/skills/
  game-architect/
    SKILL.md
    agents/openai.yaml
    references/{bootstrap,boundaries}.md
  phaser-developer/
    SKILL.md
    agents/openai.yaml
    references/{phaser4-api,runtime,playability}.md
  game-tester/
    SKILL.md
    agents/openai.yaml
    references/{test-strategy,browser-validation}.md
  pwa-github-pages/
    SKILL.md
    agents/openai.yaml
    references/{paths-and-cache,updates,ci-pages}.md
    assets/pages.yml
```

`assets/pages.yml` est un **modèle**, pas un workflow actif de ce dépôt. Il faut l'adapter au jeu et le copier dans son `.github/workflows/`. Aucun jeu, paquet npm, compte GitHub ou déploiement n'est créé par ce pack.

## Utilisation dans un projet de jeu

Copier les quatre dossiers de `.agents/skills/` dans le `.agents/skills/` du dépôt du jeu. Reprendre ou fusionner les conventions utiles de `AGENTS.md` avec les instructions existantes ; adapter sa section « Périmètre » au jeu. Ne pas écraser les instructions propres au projet.

Les skills sont sélectionnables automatiquement selon leur description et explicitement par leur nom. Le répertoire de découverte local `.agents/skills` est documenté par [OpenAI](https://learn.chatgpt.com/docs/build-skills). Pour les rendre disponibles dans tous les dépôts, le guide documente aussi `~/.agents/skills` ; ce pack n'y installe rien. Si l'interface ne reflète pas les nouveaux fichiers, redémarrer Codex.

Exemples de demandes :

```text
Utilise $game-architect et $phaser-developer pour créer un petit jeu de
survie de 60 secondes, jouable au clavier et au tactile. Avance jusqu'à
une première version jouable, testée et compilée avec cette stack.

Utilise $game-tester : après trois redémarrages, mon score augmente
plusieurs fois pour une seule collision. Reproduis, corrige et vérifie.

Utilise $pwa-github-pages pour préparer la publication sous /mon-jeu/,
vérifier l'offline et une mise à jour sans interrompre la partie.
Prépare le workflow ; ne publie pas encore.
```

Il est également possible de demander directement un jeu sans citer les skills : `AGENTS.md` fournit le routage. Les compétences restent des instructions, pas une garantie d'exécution parfaite. L'autonomie repose aussi sur les outils disponibles, les dépendances, un navigateur de test et les accès accordés. Le pack exige de distinguer ce qui a été testé de ce qui reste à vérifier.

## Choix techniques durables

- Vérifier l'API de la version Phaser **4** installée, particulièrement le rendu et les effets. Les [changements officiels de Phaser 4](https://github.com/phaserjs/phaser/releases) rendent certains exemples v3 incompatibles.
- Tester les règles avec Vitest sans démarrer le moteur ; vérifier rendu/input/physique dans un vrai navigateur. Le [Browser Mode de Vitest](https://vitest.dev/guide/browser/) complète les tests Node.
- Choisir une mise à jour PWA différable pour protéger la partie en cours ; voir le [mode prompt du plugin](https://vite-pwa-org.netlify.app/guide/prompt-for-update.html).
- Valider le vrai chemin public avant livraison ; [Vite documente la distinction entre racine et sous-chemin Pages](https://vite.dev/guide/static-deploy#github-pages).

## Entretenir le pack

Mettre à jour une référence lorsqu'un cas réel montre une lacune. Vérifier les liens officiels, les API du paquet installé et les actions épinglées avant de reprendre un modèle. Éviter d'accumuler des règles universelles issues d'un seul bug.

Pour vérifier la structure des skills avec le skill système `skill-creator`, exécuter son `scripts/quick_validate.py` sur chacun des quatre dossiers. Ce contrôle vérifie le format ; il ne prouve ni la qualité d'un futur jeu ni le succès d'un workflow GitHub. Pour évaluer le comportement, utiliser un dépôt de jeu isolé et une demande représentative, sans publier automatiquement.
