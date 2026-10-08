# EZS_orchestrator — R3.18 LAB visibility

R3.17 sait déjà sonder, claim et exécuter `Target.LAB`, et `JobHistory` sait déjà lire `runtime/jobs/lab`.

Le défaut était dans le Control Center :
- `/api/status` ne publiait que DEV et PROD ;
- `Queues & Jobs` n'affichait que DEV et PROD.

R3.18 ajoute LAB au snapshot et une troisième carte `Queue LAB`.
Aucune logique de scheduling, singleton GPU ou worker n'est modifiée.

## Application

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_LAB_VISIBILITY_R3_18.zip" `
  -C H:\EZS_orchestrator `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-lab-visibility-r3_18.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-lab-visibility-r3_18.ps1
```

Redémarrer ensuite uniquement le Control Center pour charger le nouveau `web.py`.
