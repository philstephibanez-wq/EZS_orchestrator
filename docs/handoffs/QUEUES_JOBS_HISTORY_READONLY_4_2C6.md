# 4.2c6 — Historique V1 consultable sans consommation

Source V1 vérifiée dans Git : `control_center/job_history.py` (`runtime/jobs/{dev,prod,lab}/{job}/{run}/result.json` et execution.log). Cette première migration ne lit **que les result.json**, jamais execution.log ; les anciennes tentatives uniquement avec snapshot conservé peuvent être absentes. Le mtime des fichiers est indiqué, pas la date serveur de création d'un job. Aucun état en cours n'est présenté comme réel, aucune découverte des queues en attente, aucune lecture de BDD d'applications.

Raccordement PHP `LegacyJobHistoryReader` dans page /jobs et réponse GET /api/jobs avec `source=historical_result_json`, `live_queue=false`. Loopback gardé sur l'API. Aucune écriture ni claim, ni transport réseau, ni workers Messenger. Les fichiers source ne sont pas déplacés.

Gate MAIN : test PHP, syntaxe PHP sur nouveaux fichiers, /jobs HTTP 200, /api/jobs (localhost) et observation d'une éventuelle liste de snapshots. Les lignes archivées ne remplacent pas la file temps réel V1. Aucun job LAB #181/#182/#185 consommé.
