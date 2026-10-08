# EZS_orchestrator R3.17C — tests hotfix only

À appliquer sur R3.17A + R3.17B déjà présents.

Ce hotfix corrige uniquement quatre tests historiques devenus obsolètes par
rapport au code production actuel.

Aucun fichier de production n'est modifié.

## Corrections

1. `test_orchestrator_v1_0_4_header.py`
   - retrait de l'assertion sur l'ancien texte exact du header ;
   - les assertions structurelles du header restent présentes.

2. `test_orchestrator_v1_0_7_3_deploy_modal.py`
   - le contrat vérifie les deux instructions JS séparément ;
   - il ne dépend plus de leur minification sur une seule ligne.

3. `test_r3_3_claim_failure_cleanup.py`
   - le fake executor accepte `on_progress=None`, comme l'API production actuelle.

4. `test_r3_12_dev_php_x64.py`
   - DEV et PROD attendent désormais explicitement
     `H:\PHP\php-8.5-x64\php.exe`, cohérent avec `runtime.json` et le contrat V1.0.

## Application

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_LAB_R3_17C_TESTS_HOTFIX.zip" `
  -C H:\EZS_orchestrator `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-lab-r3_17c-tests-hotfix.ps1
```

Puis suite complète :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-lab-r3_17c-tests-hotfix.ps1
```

Ne redémarrer le service permanent qu'après `EZS_ORCHESTRATOR_FULL_REGRESSION_OK`.
