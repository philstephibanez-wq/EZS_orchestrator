# V1.3b7 — Exclusion entre processus et récupération après arrêt brutal

- Ajout d'un test PHP durable `web/tests/ExclusiveLeaseCrashTest.php` (fixture sous `web/tests/fixtures/`). Sur MAIN, le parent lance un processus PHP indépendant, attend une confirmation de verrou actif, vérifie qu'un concurrent est refusé, tue le détenteur sans libération normale et vérifie la réacquisition du même verrou. Scopes `control` et `gpu-executor`. Timeout borné ; fichiers temporaires dans TEMP uniquement. Aucun job ni service métier démarré.
- La classe `ExclusiveLease` exige deux arguments scalaires (chemin persistant et scope). Elle est exclue de l'enregistrement automatique Symfony tant qu'une fabrique/runtime canonique ne les fournit pas. Cela évite une instanciation accidentelle ou la configuration de chemins temporaires en exploitation.
- Commandes MAIN : `php web/tests/ExclusiveLeaseTest.php` et `php web/tests/ExclusiveLeaseCrashTest.php`, puis `php web/bin/console lint:container`.
- Gate inchangé : mutex Python historiques et verrous PHP distincts, impossible de faire coexister deux exécuteurs de jobs. Intégration effective et bascule exclusive obligatoires avant suppression des scripts Python. Aucun remplacement de la coordination scientifique par ce lot.
- `composer.lock` généré sur MAIN non encore committé : à fournir pour intégration revue (ne pas supprimer).
