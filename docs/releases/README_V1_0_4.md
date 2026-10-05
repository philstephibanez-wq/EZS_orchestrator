# EZS Orchestrator V1.0.4 — Header polish

Correctif ergonomique ciblé, sans modification backend.

## Changements
- ajout d'un vrai header sticky ;
- identité `EZS ORCHESTRATOR` dans le header ;
- vue courante clairement séparée ;
- badge d'état global (`Système disponible` / `ANALYSE ACTIVE`) ;
- timestamp du dernier snapshot ;
- bouton global `Actualiser` ;
- responsive compact ;
- sidebar, queues, jobs, logs et déploiement inchangés.

## Installation
```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_4_HEADER_POLISH.zip" `
  -C H:\EZS_orchestrator
```

## Validation
```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_4_header.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_3_sidebar.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Attendu :
```text
EZS_ORCHESTRATOR_V1_0_4_HEADER_OK
EZS_ORCHESTRATOR_V1_0_3_SIDEBAR_OK
EZS_ORCHESTRATOR_V1_0_CONTRACT_OK
```

Redémarrer ensuite le Control Center.
