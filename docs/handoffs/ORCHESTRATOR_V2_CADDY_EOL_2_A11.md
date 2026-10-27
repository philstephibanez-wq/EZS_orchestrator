# v2.a11 — contrat Caddy Windows CRLF

Observation MAIN : `caddy validate` renvoie `Valid configuration` pour la candidate, mais `SymfonyRootCaddyCandidateContractTest.php` échoue avec `CADDY_CANDIDATE_CHANGED_OTHER_SITE_OR_SECURITY_SETTING`.

Cause probable vérifiée en revue de code : la substitution du test contient un LF explicite alors que les Caddyfiles extraits sur Windows peuvent contenir CRLF. Le test compare désormais les deux sources après normalisation stricte des seules fins de ligne, avant la substitution du commentaire et du docroot. Il continue de refuser tout autre écart (sites, autorisation média, headers, sécurité, ports). Le runtime et les configurations Caddy restent inchangés.

Validation : revue statique GitHub, `php -l` et exécution du test sur MAIN encore nécessaires ; aucune bascule de port exécutée. Contrats de parité et de rollback de v2.a10 inchangés.
