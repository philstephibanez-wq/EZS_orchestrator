# EZS Orchestrator V1.0.7 — Composer Windows execution fix

Le préflight réel a résolu Composer vers :

```text
C:\ProgramData\ComposerSetup\bin\composer.BAT
```

Le moteur V1.0 lançait tous les exécutables avec `shell=False`. Sous Windows, un `.BAT/.CMD`
doit être exécuté via `cmd.exe` de manière explicite.

Ce correctif :
- conserve `shell=False` ;
- détecte `.bat` / `.cmd` ;
- exécute via `COMSPEC /d /s /c`;
- ne change aucune règle de préflight ou de déploiement.

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_7_COMPOSER_WINDOWS.zip" `
  -C H:\EZS_orchestrator
```

## Validation

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\deployment\manager.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_composer_windows.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Ensuite relancer `launch.bat`, réactualiser le préflight et seulement alors tester le déploiement.
