# v2.a42 — surveillance PHP en lecture seule

La recette FastCGI v2.a41e est validée. Avant d'autoriser un remplacement du gateway Python, un diagnostic autonome est nécessaire.

`php bin/gateway_monitor.php once` : snapshot du gateway PROD 8510 (statut HTTP/protocole, état de maintenance, PID/port/image), code retour 0 si cohérent, 1 si incident.

`php bin/gateway_monitor.php watch 5` : même diagnostic toutes les cinq secondes, alerte sur stderr en cas d'incident. Exécution au premier plan ; arrêt manuel Ctrl+C. **Aucune tâche planifiée installée**, aucun redémarrage automatique. Aucun effet sur les processus.

Les vérifications PID/port/image reposent sur `WindowsPortOwnership` et **ne garantissent pas l'identité complète** du processus. Elles sont réservées à l'observation. Un véritable gestionnaire PHP et un rollback avec identité robuste restent à implémenter avant bascule. SSO réel et transfert médias restent bloquants.

Contrat : `php tests/GatewayMonitorContractTest.php`.
