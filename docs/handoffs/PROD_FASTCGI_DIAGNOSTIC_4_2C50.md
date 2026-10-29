# EZS Orchestrator v4.2c50 — Diagnostic FastCGI PROD

## Cause du chantier
Après redémarrage Windows le 29 octobre 2026 : état PROD périmé, récupération réussie, puis échec `EZS_PROD_START_FAILED_php_pid` sur 8512. Un diagnostic manuel montre PHP-CGI 8.5.11 présent et un socket parfois `CLOSED` sans ligne stderr. Le port 8512 accepte une liaison et une connexion TCP native .NET ; aucune réservation Windows déclarée. La cause de la perte d'écoute PHP reste à établir, pas de contournement.

## Changement circonscrit
`scripts/start.ps1` capture stdout/stderr des deux processus PHP-CGI PROD (8512 et 18515) dans `[IO.Path]::GetTempPath()/EZS_PROD_FASTCGI_4_2C50`, noms uniques horodatés. Sur échec d'attestation : état du processus, identité executable/commande, détection des listeners, PIDs propriétaires et joignabilité TCP. Ne journalise pas les arguments du processus ni les secrets. Le marqueur `EZS_PROD_START_FAILED_<name>` reste inchangé. Refus fail-closed et rollback limité aux processus lancés et identifiés restent inchangés.

## Hors périmètre
Aucun autostart Windows, aucun changement de ports ni d'architecture PHP/Caddy, aucun changement de DEV/LAB/Assistant, aucune bascule en mode normal. PROD demeure en maintenance dès qu'elle est lancée. L'autostart sera traité après diagnostic.

## Contrôle MAIN
```powershell
cd H:\EZS_orchestrator
git status --short
git pull --ff-only origin master
Get-Content .\VERSION
php tests\ProdFastcgiDiagnostic42C50ContractTest.php
php tests\ProdPhpOnly42C48ContractTest.php
.\scripts\start.ps1 -ProdAction status
```
Après vérification de ports libres et sans service PROD existant, une seule tentative contrôlée : `./scripts/start.ps1 -ProdAction start`. En cas de refus, communiquer les lignes `EZS_PROD_FASTCGI_DIAG_OUTPUT`, `EZS_PROD_START_ATTESTATION_FAILED` et le contenu du fichier stderr nommé (masquer les données sensibles). Ne pas relancer en boucle. Test Windows de démarrage non encore validé pour cette version.

## Validation
Test statique présent. Validation effective de PowerShell et de l'exploitation sur MAIN requise. Ne pas clore l'incident avant la recette.
