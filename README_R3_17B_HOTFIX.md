# R3.17B HOTFIX

Correctif à appliquer **sur R3.17A déjà installé**.

Il corrige exactement les 6 erreurs observées lors du premier apply :

- `ExecutionPlanner` redevient compatible avec les anciens fixtures de tests
  `SimpleNamespace` qui ne possèdent pas encore l'attribut `lab`.
- `_FakeExecutor` de `test_r3_2_explicit_target.py` accepte désormais
  `on_progress=None`, conformément à l'API réelle déjà utilisée par
  `OrchestrationService.run_once()`.

Aucun changement de comportement production DEV/PROD.

Aucune modification :
- runtime DEV/PROD ;
- ports ;
- Python ;
- transport ;
- lifecycle PROD ;
- Caddy ;
- deployment ;
- mutex GPU.

## Application

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_LAB_R3_17B_HOTFIX.zip" `
  -C H:\EZS_orchestrator `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-lab-r3_17b-hotfix.ps1
```

Puis :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-lab-r3_17b-hotfix.ps1
```

Ne redémarrer le service permanent qu'après suite complète verte.
