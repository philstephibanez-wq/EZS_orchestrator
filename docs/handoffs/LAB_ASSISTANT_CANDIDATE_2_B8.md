# v2.b8 — première étape de restauration LAB + Assistant sur MAIN

Diagnostic MAIN : absence de services/tâches dédiés et d'écoute 8701,8702,8712,8713,8720. EZScore DEV badge et SSO OK. Le contrat `MAIN_ONLY_CADDY_2026_10_27` impose Caddy DEV partagé; pas de XPS.

Cette livraison ajoute (1) un **Caddyfile candidat isolé** reprenant sans altération les routes actuelles 8790/8852/8502 et ajoutant LAB 8702→8701, Assistant 8712→8713 ; (2) un lanceur autonome `scripts/lab-assistant.ps1` (actions preflight, status, start) pour deux PHP-FastCGI MAIN avec verrou et attestation PID + listener + chemin + commande + création ; (3) test statique. Ne modifie **pas** le Caddyfile actif, `scripts/start.ps1`, le SSO, PROD, les modèles, le worker scientifique, Qwen ni les dépôts LAB/Assistant.

Important : **la façade LAB/Assistant ne deviendra pas accessible avec cette seule étape** ; il faut préalablement valider et commuter le candidat Caddy avec les tests non-régression SSO/médias. Ne pas utiliser les anciens start.ps1 LAB/Assistant (orchestration Python/Caddy XPS). Aucun déploiement, aucun Caddy reload automatique.

Recette MAIN sans mutation: `git pull --ff-only origin master`; `php tests/LabAssistantCandidate2B8ContractTest.php`; `powershell -ExecutionPolicy Bypass -File .\scripts\lab-assistant.ps1 -Action preflight`. Si préflight OK, `-Action start` démarre seulement les PHP-CGI (8701/8713), sans façade tant que la bascule Caddy n'est pas effectuée. Tests d'intégration, UI LAB/Assistant et vérification Qwen restent à faire. Aucun test MAIN exécuté à publication.

Attention aux variables d'environnement de secrets LAB/Assistant (tokens LAB, DB, etc.) : le lanceur ne les définit ni ne les expose. Il faudra valider les environnements hérités, santé Symfony et workers avant d'annoncer un service opérationnel.
