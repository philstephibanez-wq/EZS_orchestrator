# v2.b4 — diagnostic des pages DEV après démarrage FastCGI

MAIN v2.b3 : contrat OK et 8602/8862 initialement libres, mais START échoue avec `EZS_DEV_APP_HTTP_NOT_READY` après lancement FastCGI. Les enfants sont nettoyés par le rollback, sans fichier app-backends.json confirmé. Ce défaut ne démontre pas que les ports PHP ne fonctionnent pas ; il démontre que la vérification `/fr/login` a échoué pour au moins une façade.

Le contrôle HTTP renvoie désormais le **code par façade** via `EZS_DEV_HTTP_CHECK port=8502 status=N path=/fr/login` et idem 8852. Les échecs réseau indiquent aussi une catégorie de transport. Le critère de succès reste strict (2xx/3xx/401/403). Les HTTP 404, 500, 502, 503 et les échecs réseau refusent toujours le démarrage ; aucun contournement de l'absence de page et aucun effet PROD. Aucun corps HTML, cookie ni jeton n'est publié.

Recette MAIN : pull ; `php tests/DevHttpStatusDiagnostics2B4ContractTest.php`; `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`. Transmettre les deux lignes `EZS_DEV_HTTP_CHECK` et le résultat du lancement. Si un listener 8602/8862 appartient à une instance orpheline, ne pas tuer sans attestation ; le script refusera son adoption.

Ceci est un diagnostic ciblé, **pas une prétendue résolution HTTP** tant que le code précis et le journal du backend ne sont pas établis.
