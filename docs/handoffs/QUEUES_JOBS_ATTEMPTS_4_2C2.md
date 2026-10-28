# Migration Queues & Jobs — 4.2c2 : projection des attempts V1

Le premier composant métier-neutre PHP/Symfony du chantier est `src/Module/Coordination/JobAttemptProjection.php`. Il est **pur** : ne lit aucune BDD, ne crée, réclame, finalise ni n'exécute aucun job. Il applique le contrat attesté par Orchestrator #8 et #11.

- queued / running visibles séparément.
- completed = worker RC 0 ET callback finalisation confirmé.
- finalize_error = worker RC 0 ET callback finalisation en erreur.
- failed = worker en erreur, finalisation non tentée.
- target limité DEV/PROD/LAB ; champ erreur limité dans la projection ; aucune donnée métier ajoutée.
- Les retries ambigus, statuts intermédiaires supplémentaires et la persistance restent explicitement hors de cette première étape. Ne pas interpréter cette projection comme le moteur complet ou comme une preuve d'exactitude de tous les anciens payloads V1.

Validation locale hors MAIN : exécution PHP du test de contrat et vérification de syntaxe **sur une copie de la logique** avant publication. Test MAIN à exécuter. Aucun code du contrôleur `/api/jobs` n'a été modifié : il continue à répondre 503 plutôt que présenter une file inventée.

Gates suivants : retrouver les schémas persistés historiques et définir le modèle durable job/attempt, puis transaction de claim/lease avant connexion Messenger. Aucune action sur les jobs LAB #181/#182/#185, PROD, Assistant ou sur les scripts START/STOP v4.2b.
