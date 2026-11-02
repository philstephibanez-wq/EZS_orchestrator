# 4.2d15 — Contrat de preuve négative d'exécution

`ExecutorStopAttestor` refuse toute récupération sans identité durable fournie par une autorité indépendante : `id`, `claim_generation`, `node`, `pid`, `created_at` du processus et `instance_id` de lancement. Il confronte une observation externe à ces champs et n'accepte que `stopped_confirmed` avec identité entièrement concordante. Déconnexion, information manquante, PID réutilisé, processus actif ou erreur de sonde donnent `false`.

**Limitation bloquante** : ce composant n'est PAS une autorité d'attestation en lui-même. Les champs d'identité ne sont pas encore enregistrés avec `claim()` dans `GlobalQueueStore`. Aucune sonde Windows/XPS réelle ne lui est raccordée, et aucun sweep n'est planifié. Il est interdit de considérer un `stopped_confirmed` fabriqué par le producteur comme une preuve. L'implémentation opérationnelle exigera un registre de lancement durable détenu par le superviseur et une sonde indépendante avec attestation d'arrêt/fencing, y compris pour les descendants GPU.

Ce lot n'active aucun worker ni transport Messenger, ne manipule pas la queue MAIN et n'agit pas sur les processus DEV/PROD. Tests unitaires avec doubles de sondes ; aucun PID réel n'est inspecté ni arrêté.
