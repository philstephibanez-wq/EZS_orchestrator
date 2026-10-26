# Orchestrator v1.3a(15) — santé Docker MAIN

Le statut ERREUR de la supervision est distinct de l'état réel des services. Résolution explicite de docker.exe via PATH ou H:/Docker/Desktop/resources/bin/docker.exe, puis santé CUDA vérifiée sur `/health` et Web sur `/`. Aucune commande de redémarrage, de téléchargement ou d'analyse lancée par la sonde.

Recette MAIN : `python -m unittest discover -s tests -p test_main_supervisor.py`; GET `http://127.0.0.1:8700/api/assistant/supervision/status` après rechargement du seul Control Center ; inspecter le champ `error` si le statut reste ERROR. Ne pas toucher aux conteneurs ni à LAB, DEV, PROD.
