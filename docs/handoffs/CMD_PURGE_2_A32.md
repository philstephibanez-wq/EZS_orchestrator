# v2.a32 : retrait des wrappers CMD

Supprimés : `scripts/start.cmd`, `scripts/stop.cmd`. Les points d'entrée physiques restants sont `scripts/start.ps1` et `scripts/stop.ps1`. Le script `status.cmd` a déjà été supprimé en v2.a27 ; utiliser `php bin/infrastructure.php status`.

Ne pas retirer les PS1 de cycle de vie ni `runtime_components/prod_gateway/server.py` avant remplacement et vérification à froid : la passerelle Python occupe le port PROD 8510 et porte la politique de maintenance, les routes internes et les en-têtes OAuth/proxy. PROD et DEV ne sont pas modifiés par ce commit.

Contrat : `php tests/NoLegacyCmdWrappersContractTest.php`.
