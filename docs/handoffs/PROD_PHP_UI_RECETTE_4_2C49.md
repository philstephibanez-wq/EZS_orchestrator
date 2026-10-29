# v4.2c49 — Recette PROD PHP-only et supervision

## Périmètre
Suite à v4.2c48, PROD a été redémarrée avec les cinq composants PHP/Caddy et sans Gateway Python. La recette Windows du 29 octobre 2026 confirme : `EZS_PROD_START_MAINTENANCE_OK`, puis `EZS_PROD_STATUS ready=True state_present=True`. Les sondes de lecture seule confirment : Gateway status 200 (protocole v3, maintenance true), Gateway health 200, backend Symfony catalogue 200, façade publique catalogue 503, API supervision 200 (gateway/backend/caddy true, maintenance true).

## Correctifs
- Test contractuel `tests/ProdPhpOnly42C48ContractTest.php` : fin de section PROD détectée par le marqueur stable `EZS_PROD_STOP_OWNED_OK`, non par une mise en page particulière des scripts. Contrôle du Gateway PHP et interdiction du Gateway Python.
- `public/assets/ezs-prod-control.js` : le statut maintenance et la façade sont synchronisés dans les résumés et les détails, y compris en cas d'échec de sonde.
- `VERSION` passe à 4.2c49.

## Invariants
Aucune modification de `scripts/start.ps1`, `scripts/stop.ps1`, des configurations Caddy ni des composants applicatifs. DEV, LAB et Assistant préservés. PROD conserve son mode maintenance; l'accès public normal n'est pas réouvert par ce correctif. Pas de Python pour le Gateway.

## Recette à faire sur MAIN après pull
```powershell
cd H:\EZS_orchestrator
git pull --ff-only origin master
Get-Content .\VERSION
php tests\ProdPhpOnly42C48ContractTest.php
.\scripts\start.ps1 -ProdAction status
```
Attendus : `4.2c49`, `EZS_PROD_PHP_ONLY_4_2C48_OK`, `EZS_PROD_STATUS ready=True state_present=True`. Recharger le navigateur avec Ctrl+F5 et confirmer que le détail Maintenance affiche « Activée ».

## Statut
Recette d'exploitation PROD (maintenance) validée par sorties Windows fournies. Le test contractuel et l'affichage 4.2c49 restent à exécuter sur MAIN. Vérification SSO/médias et décision explicite requises avant sortie de maintenance.
