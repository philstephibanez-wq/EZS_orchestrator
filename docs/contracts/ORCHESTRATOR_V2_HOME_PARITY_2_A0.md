# Contrat v2.a0 — accueil historique et retrait Python intégral

Décision du 27/10/2026 : l'accueil demandé est **la vraie page historique**, non une preview ni un tableau réduit. Le projet cible est **une seule application PHP 8.5 / Symfony MVC à la racine** et **zéro fichier .py suivi par Git** à la fin du chantier.

## Source de vérité
- `control_center/web.py` : accueil réel historique à `127.0.0.1:8700` ; HTML/CSS/JS avec sidebar repliable, tableaux, jobs, incidents, logs, déploiements et supervision.
- API historiques requises : `/api/status`, `/api/jobs`, `/api/logs`, `/api/action`, `/api/deployment/*`, `/api/assistant/*`. La façade Symfony partielle sur 8790 n'a **pas** cette parité.
- Porter exactement le visuel, la navigation et les comportements dans `templates/` + `public/assets/`, puis les endpoints dans des Controllers minces et services Symfony.

## Retrait intégral obligatoire
- Tous les `*.py` versionnés sont des **dettes de migration bloquantes**, y compris les tests et scripts. Aucun ne doit subsister dans `EZS_orchestrator` au jalon final ; aucun wrapper Python, PowerShell ou CMD dans l'exécution Symfony.
- Inventorier puis remplacer **par module** avec preuves avant retrait. Les composants inclus sont contrôle Web/API, lifecycle DEV/PROD, Caddy, Git/deployment, Assistant, process, queues/leases, GPU, incidents, logs, rapports, contracts et tests.
- Exclure du périmètre Symfony les moteurs musicaux/IA LAB : orchestration uniquement.
- Ne pas effacer en masse les sources Python encore appelées par le runtime actif : cela casserait l'application historique et pourrait supprimer des garde-fous de jobs et de maintenance.
- Conserver PROD en maintenance ; jobs non consommés ; pas de flash de console Windows 11. Traçabilité issues/tests/handoffs à chaque lot.
- Critères de sortie : aucun chemin `*.py` dans l'arbre Git, aucune invocation Python dans PHP/configuration/scripts de démarrage, routes réelles en parité, tests Windows et bascule Caddy validée, rollback disponible.

## État au 27/10/2026
Symfony root bootable et testé en HTTP in-process ; accueil MVC complet et endpoints historiques **non migrés** ; les modules Python restent actifs. Le chemin 8700 reste historique tant que la parité n'est pas prouvée. **Ce document est une obligation et un suivi, non un certificat de migration finie.**
