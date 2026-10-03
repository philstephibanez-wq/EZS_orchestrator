# EZS_orchestrator R2.1

Hotfix du test de modularité R2.

Le code `server_manager/manager.py` n'avait pas de dépendance vers le Scheduler.
Le test R2 cherchait naïvement le mot `scheduler` dans tout le fichier et a donc
interprété le docstring :

`No scheduler/job/analysis dependency is allowed here.`

comme une dépendance réelle.

R2.1 remplace ce test textuel par une inspection AST des imports Python.

## Installer

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_R2_1.zip" `
    -C H:\EZS_orchestrator

powershell -ExecutionPolicy Bypass `
    -File .\bootstrap-r2_1.ps1
```

Attendu :

`EZS_ORCHESTRATOR_R2_1_CONTRACT_OK`

NO PUSH avant validation.
