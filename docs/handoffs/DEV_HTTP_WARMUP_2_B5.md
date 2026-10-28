# v2.b5 — readiness FastCGI DEV et SSO préservé

Le démarrage v2.b4 de PHP-CGI 8602 atteint sa vérification HTTP, mais GET sur 8502/fr/login expire après 5 secondes. Le rollback entraîne des 502 tant que les processus sont arrêtés. Un timeout court ne prouve pas la cause du problème.

Changement : vérification HTTP réessayée pendant au plus 45 secondes par façade, timeout individuel de 10 secondes ; toujours observation des deux façades, sans court-circuit, diagnostics par code. Redirections non suivies ; 2xx, 3xx, 401, 403 acceptés ; 404 et 500 rejetés immédiatement ; 502/503 ou timeout réessayés. Pas de modification des callbacks Google, du Host, des cookies, des sessions ni des règles média. Le preview reste isolé sans SSO ni média.

Recette : pull, php tests/DevHttpWarmup2B5ContractTest.php, start.ps1 puis inspecter les codes HTTP 8502 et 8852, enfin vérifier SSO DEV via navigateur 8502 et la session effective. Aucune recette MAIN exécutée avant publication ; ce changement ne prouve pas que le problème HTTP soit résolu. Ne pas modifier PROD. Attention : STOP met PROD en maintenance conformément au contrat.
