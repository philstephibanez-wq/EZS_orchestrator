# v4.2c54 — Cycle MAIN, modes persistants et recette

Contrat final:
- `scripts/stop.ps1`: **DEV uniquement**, ne touche pas PROD, ni son mode.
- `scripts/start.ps1` sans parametre: demarre/reconcilie les couches DEV, LAB, Assistant, puis PROD (un seul Caddy :8501/:8510/:8511). Un PROD sain existant est preserve, jamais tue en aveugle.
- Mode PROD durable `H:/EZScore/var/runtime/online-gateway.json`, `maintenance` booleen. START ne le modifie JAMAIS. Si absent ou invalide: echec ferme, pas de passage automatique en normal ou en maintenance.
- `start.ps1 -ProdAction stop`: action exceptionnelle de migration PROD uniquement, identite des PIDs et confirmation HTTP 503; restaure le dernier mode enregistre APRES arret complet. Ne pas appeler `stop.ps1` pour PROD.
- Ancien schema PROD v1 (3 Caddy) peut etre preserve si actif. Migration explicite requise pour passer a v2 (1 Caddy).
- Apres reboot: les PIDs obsoletes de PROD ne sont effaces que si tous les ports requis sont libres. Les scripts DEV utilisent leurs propres gardes d'identite.
- `scripts/install_main_autostart.ps1` installe une tache planifiee Windows au **logon du meme utilisateur**, indispensable aux lecteurs H: et aux secrets DPAPI. Ne garantit PAS un demarrage avant ouverture de session.

Recette MAIN EN ATTENTE:
```powershell
cd H:\EZS_orchestrator
git status --short
git pull --ff-only origin master
Get-Content .\VERSION
php tests\ProdPhpOnly42C48ContractTest.php
php tests\ProdFastcgiDiagnostic42C50ContractTest.php
php tests\ProdTwoCaddy42C51ContractTest.php
php tests\ProdStopDispatch42C52ContractTest.php
php tests\RebootMode42C53ContractTest.php
& H:\Caddy\caddy.exe validate --config .\config\caddy\Caddyfile.prod-unified --adapter caddyfile
.\scripts\start.ps1 -ProdAction status
```
Apres preflight, pour migration v1->v2: `start.ps1 -ProdAction stop` (sous gestionnaire PROD uniquement) puis `start.ps1` (reconcilie tous). Ne PAS lancer la migration tant que l'ownership ou la maintenance ne sont pas prouves.

Enregistrement autostart: `.\scripts\install_main_autostart.ps1` apres recette et verification des chemins, acces H:, utilisateur interactif et absence d'une tache concurrente. Tester reboot/logon et constat de deux processus caddy.exe au total et les routes :8790,:8502,:8852,:8702,:8712,:8501,:8510,:8511.

IMPORTANT: publication GitHub seulement. Aucun test runtime Windows ni reboot reel execute par ce commit. Ne pas annoncer un succes en production avant recette MAIN.
