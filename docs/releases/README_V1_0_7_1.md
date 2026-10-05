# EZS Orchestrator V1.0.7.1 — ouverture navigateur unique

Correction ciblée.

## Problème
`launch_hidden.ps1` ouvre déjà `http://127.0.0.1:8700/`, tandis que
`control_center.web` ouvrait aussi le navigateur au démarrage.

Résultat : 2 onglets Chrome.

## Correction
`start_control_center.ps1` lance maintenant :

```powershell
& $Python -m control_center.web --port $Port --no-browser
```

Ainsi :
- `control_center.web` n'ouvre plus de navigateur ;
- `launch_hidden.ps1` reste seul responsable de l'ouverture ;
- `launch.bat` n'ouvre qu'un seul onglet.

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_7_1_SINGLE_BROWSER.zip" `
  -C H:\EZS_orchestrator
```

## Validation

```powershell
H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_7_1_single_browser.py
```

Puis :

```powershell
.\launch.bat
```

Attendu : un seul onglet Chrome.
