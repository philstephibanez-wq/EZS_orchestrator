# EZS Orchestrator V1.0.6 — Launch guard

`launch.bat` reste inchangé.

Le correctif porte sur `scripts/launch_hidden.ps1`.

## Nouveau contrat

Lors d'un lancement manuel :

1. le service permanent est vérifié/démarré ;
2. le listener 127.0.0.1:8700 est identifié ;
3. si c'est le Control Center EZS attendu, il est redémarré ;
4. si le port est occupé par un processus étranger, lancement bloqué — aucun kill ;
5. le Control Center actuellement installé est démarré ;
6. le nouveau listener est revalidé ;
7. le navigateur est ouvert.

Cela supprime le cas "ancienne instance Python encore en mémoire = ancienne UI servie".

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0_6_LAUNCH_GUARD.zip" `
  -C H:\EZS_orchestrator
```

## Validation statique

```powershell
H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_6_launch_guard.py
```

Attendu :

```text
EZS_ORCHESTRATOR_V1_0_6_LAUNCH_GUARD_OK
```

## Validation réelle

Avec l'Orchestrator déjà ouvert :

```powershell
$before = (
    Get-NetTCPConnection -LocalPort 8700 -State Listen |
    Select-Object -First 1 -ExpandProperty OwningProcess
)

.\launch.bat

Start-Sleep -Seconds 2

$after = (
    Get-NetTCPConnection -LocalPort 8700 -State Listen |
    Select-Object -First 1 -ExpandProperty OwningProcess
)

"BEFORE=$before"
"AFTER =$after"
```

Le PID `AFTER` doit être différent du PID `BEFORE`.

Ensuite :

```powershell
Get-CimInstance Win32_Process -Filter "ProcessId = $after" |
Select-Object ProcessId,ExecutablePath,CommandLine
```

Le process doit utiliser :

```text
H:\Python\pythoncore-3.14-64\python.exe
```

et sa ligne de commande doit contenir :

```text
-m control_center.web
```
