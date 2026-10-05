# EZS Orchestrator V1.0.7.4 — logs de déploiement visibles

Ajoute **Déploiements** dans la vue **Logs**.

## Comportement
La vue affiche :
- l'historique des déploiements ;
- état de chaque déploiement ;
- commit PROD avant → commit cible ;
- durée quand disponible ;
- journal détaillé du dernier déploiement via l'API existante.

Pendant un déploiement, la vue Logs se rafraîchit déjà périodiquement : le journal devient donc visible sans ajouter de nouveau backend.

## Audit
Le bouton **Clear logs** est désactivé sur l'onglet `Déploiements`.
L'historique de déploiement est traité comme un journal d'audit et n'est pas effacé depuis la vue Logs.

Aucun backup DB n'est exposé ni exporté par ce correctif.

## Installation
```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_7_4_DEPLOYMENT_LOGS.zip" `
  -C H:\EZS_orchestrator
```

## Validation
```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_4_deployment_logs.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Puis :
```powershell
.\launch.bat
```

Dans **Logs**, un nouvel onglet **Déploiements** doit être visible.
