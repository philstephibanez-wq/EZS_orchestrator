# EZS Orchestrator V1.0.3 — sidebar polish

Correction ergonomique ciblée, sans changement fonctionnel backend.

## Changements
- suppression du bouton `Réduire` en bas du volet ;
- ajout d'un contrôle `<<` / `>>` visible en haut ;
- `<<` = réduire, `>>` = déployer ;
- état persisté comme avant via `localStorage`;
- badge `EZ` verrouillé à 34×34 et non réductible ;
- les trois vues et toutes les API/actions V1.0 restent inchangées.

## Installation
```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_3_SIDEBAR_POLISH.zip" `
  -C H:\EZS_orchestrator
```

## Validation
```powershell
H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_3_sidebar.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py
```

Attendu :
```text
EZS_ORCHESTRATOR_V1_0_3_SIDEBAR_OK
EZS_ORCHESTRATOR_V1_0_CONTRACT_OK
```

Redémarrer ensuite le Control Center pour charger le nouveau HTML.
