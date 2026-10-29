# Handoff 4.2c23 — Noyau de persistance de queue globale

Nouveau `src/Module/Coordination/GlobalQueueStore.php` : transaction d'admission idempotente, claim atomique cpu/gpu, token lease, finish protégé et persistance SQLite WAL. Tous les producteurs dans **une seule table** ; aucun sens métier interprété.

`tests/GlobalQueueStore42C23ContractTest.php` simule deux provenances uniquement dans une DB de temp, validation de l'idempotence, collisions, claims exclusifs, reprise d'ouverture et finalisation. **Aucun test exécuté sur Windows par le commit** ; se fier à la recette mainteneur. Pas de raccordement HTTP, ni changement START/STOP, ni insertion dans registre historique. Étape suivante : attempts, heartbeat/fencing, récupération des leases et contrats producteurs avant activation.
