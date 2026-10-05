# EZS Orchestrator V1.0.7.5 — environnement PROD explicite

Le premier déploiement réel a échoué dans `composer install --no-dev`.

Cause confirmée :
- `H:\EZScore\.env` contient `APP_ENV=dev`
- `H:\EZScore\.env.local` contient `APP_ENV=dev`
- Composer retire donc les bundles DEV, puis l'auto-script Symfony `cache:clear`
  redémarre en environnement DEV et tente encore de charger `DebugBundle`.

Le déploiement ne doit pas modifier `.env.local`, qui reste une configuration cible.
Le moteur impose désormais explicitement aux commandes de déploiement :

```text
APP_ENV=prod
APP_DEBUG=0
```

pour :
- Composer + ses auto-scripts ;
- migrations Doctrine ;
- cache clear.

L'environnement explicite est aussi consigné dans le JSON de chaque étape
(sans aucune variable sensible).

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_7_5_PROD_ENV.zip" `
  -C H:\EZS_orchestrator
```

## Validation

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\deployment\manager.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_5_prod_env.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_composer_windows.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Relancer ensuite `.\launch.bat`.

Ne pas remettre PROD en mode normal avant la réparation de l'installation Composer.
