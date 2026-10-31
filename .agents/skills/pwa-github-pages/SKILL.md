---
name: pwa-github-pages
description: Configurer, vérifier et livrer un jeu Vite avec vite-plugin-pwa sur GitHub Pages via GitHub Actions. À utiliser pour les chemins de production, manifest, cache offline, mises à jour du service worker, build et CI/CD ; la préparation locale ne vaut pas autorisation de publier.
---

# PWA et GitHub Pages

Livrer un artefact reproductible qui fonctionne au chemin public prévu, hors ligne selon son contrat et après mise à jour.

## Workflow

1. Lire scripts, lockfile, version Node, config Vite/PWA, workflows, remote et domaine configuré. Déterminer l'URL cible : dépôt sous `/repo/`, site utilisateur à `/` ou domaine personnalisé. Ne pas déduire systématiquement le chemin du nom du dépôt.
2. Lire [paths-and-cache.md](references/paths-and-cache.md) pour le `base`, manifest, scope et contenu offline. Faire du chemin de base une valeur cohérente pour build, assets et PWA.
3. Lire [updates.md](references/updates.md) pour l'enregistrement et la mise à jour sans perte de partie. Préférer `generateSW` et une confirmation de mise à jour pour un petit jeu ; justifier un worker personnalisé.
4. Lire [ci-pages.md](references/ci-pages.md) pour préparer ou réparer les workflows. Les validations doivent précéder le déploiement de l'artefact exact construit.
5. Exécuter installation reproductible, typecheck, tests et build avec le chemin cible. Servir le build ; vérifier URLs, manifest et worker. Utiliser la recette offline et A/B de `game-tester` si disponible, sinon effectuer ces mêmes scénarios directement.
6. Publier seulement dans le périmètre autorisé. Après publication, vérifier le statut Actions et l'URL réellement retournée, puis le chargement du jeu et de ses assets. Si l'accès manque, livrer les fichiers prêts et préciser le réglage ou l'accès bloquant.

## Ne pas confondre

- Un manifest valide avec une PWA fonctionnelle hors ligne.
- Un `vite preview` à la racine avec une validation du sous-chemin Pages.
- Un build qui passe avec un contrôle de types qui passe.
- Un workflow écrit avec un déploiement effectué.
- Une mise à jour du service worker avec une migration de sauvegarde utilisateur.

Le service worker est désactivé en développement par défaut pour éviter des diagnostics trompeurs. Vérifier son comportement sur le build de production. Ne pas effacer globalement caches ou registrations pour « réparer » une application.
