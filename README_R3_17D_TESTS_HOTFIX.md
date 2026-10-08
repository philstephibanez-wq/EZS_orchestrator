# EZS_orchestrator R3.17D — tests hotfix

À appliquer sur la branche actuelle contenant R3.17A/B/C.

Cause exacte de l'échec R3.17C :
la fonction de migration considérait `new=""` comme déjà présent dans tout texte,
donc la suppression de l'ancienne assertion de header n'était jamais exécutée.

R3.17D :
- introduit une suppression idempotente sûre ;
- réapplique les 4 corrections de tests ;
- vérifie explicitement qu'aucune assertion obsolète ne subsiste ;
- ne modifie aucun fichier de production.

## Application

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_LAB_R3_17D_TESTS_HOTFIX.zip" `
  -C H:\EZS_orchestrator `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-lab-r3_17d-tests-hotfix.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-lab-r3_17d-tests-hotfix.ps1
```

Ne redémarrer le service permanent qu'après :
`EZS_ORCHESTRATOR_FULL_REGRESSION_OK`.
