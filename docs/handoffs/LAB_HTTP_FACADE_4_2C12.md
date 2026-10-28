# 4.2c12 — Réparation transport HTTP LAB / FastCGI
Diagnostic sur MAIN : TCP 8701 ouvert, port détenu par php-cgi.exe PID 30048 ; `curl` HTTP direct 8701 retourne `Recv failure: Connection was reset`. La config Caddy canonique expose `http://127.0.0.1:8702` avec `php_fastcgi 127.0.0.1:8701`.

Correction : `LabQueueProbe` fait désormais le GET authentifié vers la façade HTTP 8702. Ne pas modifier le backend FastCGI 8701 ni la clé du LAB.

Tests historiques 4.2c10/4.2c11 alignés sur la version 4.2c12 et sur la façade, avec racine temporaire isolée pour éviter que le scénario « pas de jeton » lise le vrai fichier LAB. Nouveau contrat statique comparant le client à Caddy. Aucun test MAIN de cette version encore exécuté.

Aucun POST claim, aucun worker, aucune opération PROD ou Assistant, aucun changement START/STOP. Une réponse HTTP 200 authentifiée doit être constatée sur MAIN avant de qualifier la connexion LAB de fonctionnelle.
