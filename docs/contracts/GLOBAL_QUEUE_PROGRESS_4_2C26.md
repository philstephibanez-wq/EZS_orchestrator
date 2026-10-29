# Contrat progression de queue 4.2c26

LAB, Assistant et ultérieurement EZScore exécutent leurs jobs localement ; Orchestrator est seul propriétaire de la queue globale et des transitions techniques. Le pourcentage provient **du worker exécutant** et n'est jamais calculé par Orchestrator. Une progression est optionnelle : null signifie indéterminée. En cours : 0–99 % ; 100 % sera lié à une finalisation confirmée dans un lot ultérieur.

Le worker détenteur du token de lease appelle `GlobalQueueStore::heartbeat(jobId, token, seconds, progressPercent?, phase?, message?)`. La méthode valide le lease actif, empêche une progression décroissante, renouvelle la réservation et écrit, **dans la même transaction SQLite**, un événement immuable. Un heartbeat sans progression est accepté. Seuls des messages courts contrôlés sont admis (pas de secrets ni logs bruts).

`events(producer,after,limit)` lit un journal durable cloisonné par producteur, avec curseur. Le paramètre producer doit provenir de l'authentification REST future, **jamais d'un paramètre utilisateur non vérifié**. Cette tranche n'expose aucune route HTTP ni SSE, et ne consomme aucun job réel. La gestion des tentatives, la récupération de lease expiré, le callback métier et la finalisation avec événement complet restent hors périmètre.

Fichier permanent : `data/queue/global.sqlite`, réservé à Orchestrator. Les tests utilisent uniquement une base temporaire.
