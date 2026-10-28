# v2.a40 — préparation d'une façade Caddy + PHP-FastCGI

La passerelle Python PROD reste active sur 8510 et la façade publique PROD continue de la cibler.

Une configuration **candidate non déployée** `config/caddy/Caddyfile.gateway-php-candidate` prépare Caddy sur localhost 18514 et PHP-FastCGI sur 18515. Aucun processus n'est lancé par ce patch. Un préflight en lecture seule est disponible : `php bin/gateway_fastcgi_candidate.php`.

**Point de blocage majeur identifié :** sous Caddy, la directive `rewrite * /router.php` peut modifier `REQUEST_URI`. La parité 10/10 établie avec le serveur PHP intégré ne prouve donc pas la parité d'URL avec FastCGI. Le candidat doit intégrer un transport fiable de l'URI originale, être testé et contrôlé avant tout démarrage permanent.

Autres prérequis : superviser 18515, valider en conditions réelles OAuth/cookies/médias, vérifier l'identité complète du processus et tester le retour arrière. La candidate n'autorise aucune bascule PROD.

Recette initiale sans démarrage :
```powershell
php -l bin\gateway_fastcgi_candidate.php
php tests\GatewayFastcgiCandidateContractTest.php
php bin\gateway_fastcgi_candidate.php
```
