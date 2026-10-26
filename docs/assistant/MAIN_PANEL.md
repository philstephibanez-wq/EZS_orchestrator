# Panneau Orchestrator — Assistant MAIN v1.3a(14)

Le panneau reflète les données de `/api/assistant/supervision/status` v2 : statut Web et CUDA sur MAIN, sans présenter les workers XPS périmés comme Assistant actif. `/api/assistant/deployment/status` retourne `DISABLED_MAIN_DOCKER` ; le bouton XPS est désactivé dans l'interface comme dans l'API.

Adresse Assistant Web MAIN : http://127.0.0.1:18713/ ; Qwen technique : http://127.0.0.1:18720/ ; Orchestrator : http://127.0.0.1:8700/.

Validation MAIN requise après pull : `python -m py_compile control_center/web.py`, redémarrage du seul Control Center, actualisation forcée navigateur, vérification des endpoints de supervision et déploiement. Aucun redémarrage LAB, DEV, PROD ou CUDA. Non lié au workflow métier LAB–Assistant, toujours non livré.
