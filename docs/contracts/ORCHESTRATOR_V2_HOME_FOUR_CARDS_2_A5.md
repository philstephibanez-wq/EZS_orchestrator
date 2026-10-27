# Contrat accueil Orchestrator — v2.a5

L'URL `/` de Symfony racine rend `templates/infrastructure/index.html.twig` : sonde GPU latérale `_gpu_monitor.html.twig` et les quatre pavés DEV EZScore, PROD EZScore, LAB EZStudio, Assistant. Le template `legacy_home.html.twig` est conservé dans le dépôt uniquement pour référence et son test de parité statique, mais ne constitue plus l'accueil actif. Cette décision corrige le choix erroné de template observé sur MAIN.

Les contrôles HTTP in-process et preview inspectent les quatre pavés et le panneau GPU. Le test de preview continue de vérifier l'identité Symfony depuis `/api/status` et le blocage explicite des jobs depuis `/api/jobs`.

Aucune activation des actions non migrées, aucune modification du Caddy, des ports, du cycle de vie, de PROD, ni suppression de `web/`. La sonde GPU reste soumise à ses restrictions DEV/loopback existantes. Les tests Windows de rendu réel restent à exécuter sur MAIN.
