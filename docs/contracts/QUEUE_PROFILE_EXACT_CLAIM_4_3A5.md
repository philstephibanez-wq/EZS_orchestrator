# Orchestrator 4.3a5 — Sélection exacte de PROFILE et identité d'exécution

- Ajoute aux **anciens** champs `resource_class` / `lease_seconds` une variante strictement optionnelle `job_id` + `kind=profile`, uniquement pour la ressource `gpu`. Les anciennes requêtes et clients restent compatibles.
- `QueueExecutorProtocol::claim` vérifie `producer=lab`, `kind=profile`, `resource_class=gpu` avant de déléguer au noyau `GlobalQueueStore::claim(..., ?onlyJobId)`. Le noyau conserve transaction `BEGIN IMMEDIATE`, slot GPU unique, priorité lorsque aucun ID n'est fourni et protection des leases.
- Ajoute `POST /api/v2/queue/executor/ownership` : uniquement loopback, flag `EZS_QUEUE_EXECUTOR_API=1`, secret exécuteur distinct, schéma exact, preuve PID + date WMI observée par le lanceur, puis inscription immuable via `ExecutorOwnershipRegistry` dans la **même** SQLite canonique. Aucun moteur scientifique et aucun endpoint de résultat LAB n'est ajouté dans Orchestrator.
- L'API de réception `finish` 4.3a4 reste inchangée ; un reçu LAB signé et une génération/lease courants demeurent requis.
- Aucune activation au déploiement. Aucune récupération automatique sur seule absence de PID. Les enfants éventuels demeurent bloquants jusqu'à attestation indépendante.
- Impact : seul `GlobalQueueStore`, `QueueExecutorProtocol`, nouveau contrôleur, tests et VERSION. Pas de nouveau service, port, tâche planifiée ou changement PROD.
- Tests MAIN exigés : PHPUnit ciblé et complet, `lint:container`, `lint:twig`, HTTP disabled/unauthorized et inscription immuable, preflight Git, version et SHA, validation de processus Windows réelle avant mise en service.
