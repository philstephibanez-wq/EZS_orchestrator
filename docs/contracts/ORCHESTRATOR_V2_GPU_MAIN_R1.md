# Module GPU MAIN — V1.3b5
- PHP/Symfony : `GpuProbe` est propriétaire de la sonde MAIN `nvidia-smi`. Le parser est testable sans GPU, le processus a un délai maximal de cinq secondes.
- REST `GET /api/v2/gpu/main` ; authentification fail-closed par `EZS_GPU_REST_TOKEN` (en-tête `X-EZS-GPU-Token`), aucune valeur de secret committée ; erreurs génériques, sans sortie de commande ni chemins locaux divulgués.
- Aucun service démarré, aucune tâche Windows, aucune sonde distante ni nouvelle CLI métier. L'API n'est **pas déployée** ; Caddy et l'autorisation transversale doivent encore être validés.
- La déduplication avec les sondes LAB et Assistant MAIN doit se faire **après** migration de leurs consommateurs vers REST et tests HTTP. Ne pas retirer les routes actives prématurément.
- Dépendance `symfony/process: 7.4.*` à installer sur MAIN, puis mettre à jour `composer.lock` local sans le supprimer ; lock à auditer/versionner. Contrat statique : `php web/tests/GpuTelemetryParserTest.php`, `php -l` des classes et `debug:router`.
- Aucun job scientifique, moteur, preset, audio ou donnée SQLite touché. Tests de runtime non exécutés sur MAIN à la publication.
