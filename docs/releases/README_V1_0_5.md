# EZS Orchestrator V1.0.5 — Header global + vue Logs

- vrai header global pleine largeur ;
- identité `EZS ORCHESTRATOR V1.0` ;
- aucune mention `local` ;
- sidebar avec 4 vues :
  - Infrastructure
  - Queues & Jobs
  - Logs
  - Déploiement
- logs retirés d'Infrastructure et déplacés dans une vue dédiée ;
- `<< / >>` conservé ;
- backend et API inchangés.

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_5_HEADER_LOGS.zip" `
  -C H:\EZS_orchestrator
```

## Validation

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_5_header_logs.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Attendu :
```text
EZS_ORCHESTRATOR_V1_0_5_HEADER_LOGS_OK
EZS_ORCHESTRATOR_V1_0_CONTRACT_OK
```
