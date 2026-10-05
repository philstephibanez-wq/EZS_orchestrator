# EZS Orchestrator V1.0.7.2 — feedback préflight Déploiement

Le bouton **Actualiser l'analyse** fonctionnait sans aucun retour visuel avant la fin de `/api/deployment/plan`.
Comme le préflight peut effectuer un `git fetch`, cela donnait l'impression que le bouton ne faisait rien.

## Correction
- clic => bouton désactivé et libellé `Analyse…`;
- décision => `ANALYSE EN COURS…`;
- message explicite pendant le préflight;
- restauration du bouton à la fin;
- toast de succès/blocage;
- protection contre les doubles clics.

Aucun changement backend ni règle de déploiement.

## Installation
```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_7_2_DEPLOY_REFRESH_FEEDBACK.zip" `
  -C H:\EZS_orchestrator
```

## Validation
```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_2_deploy_refresh_feedback.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Puis relancer `.\launch.bat`.
