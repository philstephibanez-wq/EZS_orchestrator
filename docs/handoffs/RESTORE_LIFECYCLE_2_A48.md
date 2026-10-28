# v2.a48 — restauration des commandes essentielles DEV

Correction de la suppression prématurée en v2.a46 : restauration **inchangée** depuis e505182 des fichiers `scripts/start.ps1`, `scripts/stop.ps1`, `scripts/v2_lifecycle.ps1`.

Le moteur commun conserve les actions `start`, `stop`, `status` et `repair`. Le retrait précédent rompait la reprise DEV, contrairement à la demande du mainteneur de préserver les commandes essentielles.

La restauration concerne uniquement DEV. Les lanceurs obsolètes `launch.bat`, `stop.bat`, `scripts/infrastructure_restore.ps1` restent supprimés ; les deux composants historiques PROD sont préservés. Pas d'arrêt/redémarrage ni modification des processus et ports par ce commit.

Recette MAIN : `git pull --ff-only origin master` puis `powershell -ExecutionPolicy Bypass -File .\scripts\v2_lifecycle.ps1 -Action status`. Ne pas lancer `start`, `stop` ou `repair` avant contrôle de l'état MAIN ; aucun test de processus live n'a été exécuté lors de la publication.
