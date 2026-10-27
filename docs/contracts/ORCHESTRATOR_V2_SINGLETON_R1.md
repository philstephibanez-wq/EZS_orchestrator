# Coordination singleton V2 — première primitive PHP (1.3b6)

## Objectif
La V1 protège le Control Center et l'exécuteur GPU via deux mutex Windows distincts. V2 doit maintenir **un coordinateur actif MAIN** et **un seul job GPU simultané**, indépendamment des requêtes HTTP concurrentes et des consommateurs Messenger.

## Primitive ajoutée, NON branchée sur le runtime
`Ezs\\Web\\Module\\Coordination\\ExclusiveLease` utilise `flock(LOCK_EX | LOCK_NB)`, deux scopes explicites `control` / `gpu-executor`, garde le descripteur pendant tout le traitement, libère sur `release()` ou destruction, et refuse l'entrée concurrente. Ne jamais supprimer un lock en utilisation. Le test utilise un dossier unique du répertoire TEMP du système, puis le supprime.

## Précautions bloquantes
- Cette primitive PHP **ne partage pas les mutex Windows nommés de V1**. Ne PAS lancer simultanément un exécuteur Python V1 et un exécuteur Symfony V2 ; établir une coupure exclusive validée au moment de la bascule.
- Aucun listener HTTP, aucun gestionnaire de jobs ni consommateur Messenger n'utilise encore cette primitive. Ce commit **ne rend PAS l'Orchestrator Symfony singleton en exploitation**.
- Vérifier sous Windows MAIN le comportement exclusif entre deux processus distincts, l'arrêt brutal, la récupération du verrou et la cohérence avec SQLite avant toute exploitation. Les locks seuls ne garantissent ni idempotence, ni reprise des leases DB.
- L'emplacement final des locks doit être durable hors du code, sous runtime de l'Orchestrator et partagé entre les travailleurs Symfony ; jamais sous H:\\temp en production.
- Interdiction des tâches planifiées Windows, de `php -S`, des CLI/launchers parallèles ; cleanup Python obligatoire après parité et cutover approuvés.

## Autres corrections de ce lot
Le parseur GPU fixe explicitement le paramètre `escape` de `str_getcsv()` pour PHP 8.5 ; `web/config/reference.php`, fichier généré, est ignoré. `web/composer.lock` **reste à versionner** depuis MAIN, ne pas le supprimer.

## Vérifications
Tests à lancer sur MAIN : `php web/tests/GpuTelemetryParserTest.php`, `php web/tests/ExclusiveLeaseTest.php`, syntaxe PHP, `debug:router`. Aucun runtime réel ou job scientifique démarré dans ce correctif.
