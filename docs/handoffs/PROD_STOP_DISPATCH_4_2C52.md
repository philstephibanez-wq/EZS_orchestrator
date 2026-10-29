# v4.2c52 — correction du dispatch STOP PROD

## Incident
Sur MAIN, apres l'installation de v4.2c51 et quatre preflights OK, `scripts/stop.ps1 -ProdAction stop` appelle `bin/prod_mode.php maintenance` puis refuse avec `prod_gateway_unavailable`. Les processus PROD ne sont pas arretes.

## Cause prouvee dans GitHub
Le dispatch de `-ProdAction` etait place dans le corps de `Invoke-EzsLabAssistantLifecycle`, et non au niveau principal du script. Par consequent `-ProdAction stop` suivait le STOP global (dev, lab, assistant) au lieu d'entrer dans `Invoke-EzsProdLifecycle`.

## Correctif
Dispatch `-ProdAction` deplace immediatement apres les declarations de fonctions et AVANT l'ancien STOP global. Aucune modification des blocs de validation PID et de maintenance dans le lifecycle PROD. Aucun changement de routes, PHP, Caddy, DEV, LAB, Assistant, jobs, worker ni base de donnees. Test statique ajoute : `tests/ProdStopDispatch42C52ContractTest.php`.

## Controle MAIN, une seule etape
```powershell
cd H:\EZS_orchestrator
git status --short
git pull --ff-only origin master
Get-Content .\VERSION
php tests\ProdStopDispatch42C52ContractTest.php
php tests\ProdTwoCaddy42C51ContractTest.php
.\scripts\start.ps1 -ProdAction status
```

Ensuite, apres lecture de ces sorties, autoriser une tentative `scripts/stop.ps1 -ProdAction stop` uniquement si les proprietaires des PIDs et l'etat maintenance peuvent etre verifies. Un retour `EZS_PROD_REFUSED_UNVERIFIED_PROCESS_OWNERSHIP` ou `EZS_PROD_STOP_REFUSED_MAINTENANCE_UNCONFIRMED` reste un refus de securite valide et ne doit pas etre contourne. Ne jamais tuer globalement Caddy.

## Etat
Publication GitHub effectuee. La recette Windows et la bascule PROD restent a faire. Ne pas conclure que le nombre de processus Caddy est conforme avant controle sur MAIN.
