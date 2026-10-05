# EZS Orchestrator V1.0.7.3 — Modale de déploiement

Remplace la popup navigateur native par une vraie modale intégrée à l'Orchestrator.

## La modale affiche
- commit PROD actuel → commit cible ;
- nombre de fichiers ;
- migrations Doctrine ;
- fichiers sensibles ;
- étapes en français compréhensible ;
- avertissement clair sur la maintenance et les données métier ;
- boutons `Annuler` et `Déployer vers PROD`.

Le jargon `quiesce worker`, `health check`, `git ff-only`, etc. est retiré de l'interface.

## Installation
```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_7_3_DEPLOY_MODAL.zip" `
  -C H:\EZS_orchestrator
```

## Validation
```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_3_deploy_modal.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Puis :
```powershell
.\launch.bat
```
