# Assistant Docker MAIN — v1.3a(13)

Le Control Center interroge les conteneurs Docker locaux Web `18713` et llama.cpp CUDA `18720`. Aucun SSH XPS. Les commandes Start/Stop ne ciblent que le conteneur WEB existant ; le GPU CUDA n'est pas démarré ou arrêté. Le déploiement historique XPS est désactivé. LAB, DEV, PROD inchangés.

Validation MAIN : `python -m py_compile control_center/web.py assistant_supervision/main_supervisor.py` puis redémarrer uniquement Control Center et interroger `/api/assistant/supervision/status`. Aucun redémarrage orchestrateur ni test MAIN n'a été effectué à la publication.

Limite : le workflow LAB→orchestrateur→Assistant et le retour métier restent à implémenter ; interface historique partiellement conservée.
