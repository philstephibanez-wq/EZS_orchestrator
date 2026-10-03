# EZS_orchestrator R1

`EZS_orchestrator` is the local orchestration layer for EZScore.

It deliberately contains **no musical-analysis business logic**.

## Responsibilities

- `control_center/`: presentation / local administration only.
- `server_manager/`: DEV / PROD server lifecycle and health.
- `scheduler/`: queues, priorities and resource arbitration.
- `executor/`: subprocess execution of the analysis code belonging to the selected EZScore checkout.
- `contracts/`: versioned neutral contracts shared by the infrastructure modules.
- `config/`: machine-local topology/configuration.
- `runtime/`: orchestrator runtime state only.
- `logs/`: orchestrator logs only.

## Hard architecture rules

1. DEV must never be able to break PROD.
2. PROD physical root is `H:\EZScore`, `APP_ENV=prod` only.
3. DEV physical root is `H:\EZScore_dev`, `APP_ENV=dev|prod`.
4. `APP_ENV=prod` on DEV still uses DEV code, DB, storage and runtime.
5. Analysis implementations stay in the EZScore checkout:
   - DEV: `H:\EZScore_dev\analysis`
   - PROD: `H:\EZScore\analysis`
6. Scheduler knows nothing about Whisper, stems, chords, beats or lyrics.
7. Executor chooses the analysis implementation from the explicit target.
8. Cross-root paths are rejected before any subprocess is launched.
9. Initial GPU capacity is one slot.
10. No silent fallback.

## R1 scope

R1 is intentionally an architecture/bootstrap release.

It provides:
- external configuration;
- server topology model;
- neutral job contract;
- scheduler with a single GPU slot;
- executor planning and DEV/PROD path guards;
- a CLI control-center smoke entrypoint;
- contract tests.

It does **not yet** migrate the existing GUI or start/stop production processes.

## Install locally

```powershell
cd H:\
New-Item -ItemType Directory H:\EZS_orchestrator -Force | Out-Null
tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_R1.zip" -C H:\EZS_orchestrator
cd H:\EZS_orchestrator
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

Expected:

`EZS_ORCHESTRATOR_R1_BOOTSTRAP_OK`

## Tests

```powershell
cd H:\EZS_orchestrator
H:\Python\pythoncore-3.14-64\python.exe -m unittest discover -s tests -v
```

Expected final result:

`OK`

## Smoke

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli status
```

Expected to print the DEV/PROD topology and `GPU slots: 1`.

## Git initialization

Create an empty GitHub repository named `EZS_orchestrator`, then:

```powershell
cd H:\EZS_orchestrator
git init
git add .
git commit -m "R1 modular orchestrator bootstrap"
git branch -M master
git remote add origin https://github.com/philstephibanez-wq/EZS_orchestrator.git
git push -u origin master
```

Do not migrate the historical EZScore worker code into this repository wholesale. Migrate module-by-module behind the contracts in this R1.
