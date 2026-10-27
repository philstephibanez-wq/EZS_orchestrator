# v1.3b30 — façade 8502 candidate, sans activation

## Préflight MAIN
Le Caddy DEV actif, PID 28860 lors du dernier test, conserve `admin off`, donc un `caddy reload` ne doit pas être présenté comme immédiatement utilisable. Ses sites effectifs sont Orchestrator 8790 et preview 8852. La configuration historique EZScore 8502 attend un backend HTTP 8602 et utilise `forward_auth /internal/media/auth` et `{$EZSCORE_MEDIA_ROOT}` avant `file_server` pour les médias. Le nouveau backend `php-cgi.exe -b 127.0.0.1:8602` est en revanche FastCGI, **pas HTTP**. Brancher `reverse_proxy` / `forward_auth` sur ce port ne fonctionnerait pas.

Le fichier `web/config/caddy/Caddyfile.dev-candidate` contient donc uniquement une **configuration candidate inactive**, qui reprend à l'identique les deux sites du Caddy partagé et ajoute le site historique EZScore 8502 protégé. Le fichier actif `Caddyfile.dev-preflight` est volontairement inchangé. **Ne pas lancer la candidate** en présence du listener FastCGI 8602. Les tests statiques vérifient les protections et l'absence de PROD.

## Préconditions avant activation ultérieure
Résoudre la propriété/état de 8602 ; décider et tester le backend HTTP 8602 ou un adaptateur HTTP d'authentification pour les médias avec FastCGI ; valider la configuration avec `H:\Caddy\caddy.exe validate --config ... --adapter caddyfile` et vérifier la valeur de `EZSCORE_MEDIA_ROOT` hors dépôt ; définir la stratégie d'activation de `admin off` (un basculement initial contrôlé est nécessaire avant toute gestion dynamique) ; prouver SSO/media et HTTP 8502, sans impacter l'instance PROD. Aucun redémarrage autorisé par le présent commit.
