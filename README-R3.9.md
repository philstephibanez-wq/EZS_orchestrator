# EZS_orchestrator R3.9 - Visual Control Center

Interface locale sur `http://127.0.0.1:8700/`.

Fonctions : statut service, GPU, backend DEV, Caddy DEV, queues DEV/PROD, logs et actions DEV.
PROD est volontairement en lecture seule.

Installation :

```powershell
cd H:\EZS_orchestrator
tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_R3_9_VISUAL_CONTROL_CENTER.zip" -C H:\EZS_orchestrator
powershell -ExecutionPolicy Bypass -File .\bootstrap-r3_9.ps1
```

Lancement :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_control_center.ps1
```
