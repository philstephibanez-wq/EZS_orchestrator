# 4.2c11 — Résolution sûre du jeton LAB sur MAIN

Capture MAIN 4.2c10 : carte « File LAB — Non connectée », raison `token_not_configured`. Cause vérifiée sur GitHub : `LabQueueProbe` ne cherchait que `getenv('EZS_LAB_ANALYSIS_TOKEN')` ; la source canonique LAB est `H:\\EZStudio_lab\\.env.local` avec `EZSTUDIO_ANALYSIS_WORKER_TOKEN`, validée dans `LabAnalysisTokenGuard`.

Ordre de résolution : variable d'environnement explicite Orchestrator si présente, sinon lecture locale de la valeur LAB dans son .env.local (uniquement en mémoire, jamais Git/log/UI), sans exporter ni copier le secret. Token absent/invalide : aucune requête émise et statut non connecté. Aucun changement dans LAB ni Assistant.

Le transport reste strictement GET sur loopback 8701, sans claim ou dispatch, et sa disponibilité réelle après déploiement n'est pas prouvée. Le jeton du test est entièrement synthétique dans un répertoire temporaire système et les traces ne contiennent aucune valeur de production. Pas de redémarrage imposé : la valeur est relue par requête.

Recette MAIN : php -l et test dédié, GET /jobs et observation de la carte LAB ; si le token canonique local est absent, diagnostiquer le provisioning sans jamais transmettre sa valeur. Contrat global START/STOP inchangé.
