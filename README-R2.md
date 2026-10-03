# EZS_orchestrator R2 — infrastructure split

R2 is the first functional infrastructure extraction from the historical EZScore Worker.

It intentionally does **not** move musical analysis code into this repository.

## What moves in R2

### `server_manager/`
Owns:
- physical DEV / PROD topology;
- APP_ENV validation;
- exact PHP backend process ownership;
- start / stop / restart / status / health;
- PID/meta files stored only in `H:\EZS_orchestrator\runtime`.

It does not know jobs, CUDA, Whisper, stems, chords or lyrics.

### `transport/`
Owns:
- neutral HTTP communication with each EZScore instance;
- target-specific token discovery from the target checkout `.env.local`;
- worker hello / heartbeat / queue / claim / progress / complete / fail endpoints.

It does not schedule and does not execute analysis.

### `scheduler/`
Owns:
- queue arbitration;
- priorities;
- GPU capacity.

It has no musical-analysis imports.

### `executor/`
Owns:
- explicit target root resolution;
- cross-root path guards;
- subprocess lifecycle.

The analysis implementation is always taken from:
- DEV: `H:\EZScore_dev\analysis`
- PROD: `H:\EZScore\analysis`

R2 does not yet execute live EZScore jobs because the neutral business entrypoint
`analysis/worker_entrypoint.py` is deliberately left to EZScore, where it belongs.

## Safety invariant

**DEV can never mutate or stop PROD implicitly.**

There is no restore-on-start behavior in the orchestrator.

Every PROD start/stop/restart is an explicit command.

## Install

Overlay onto the R1 checkout:

```powershell
cd H:\EZS_orchestrator
tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_R2.zip" -C H:\EZS_orchestrator
powershell -ExecutionPolicy Bypass -File .\bootstrap-r2.ps1
```

Expected:

```text
EZS_ORCHESTRATOR_R2_CONTRACT_OK
```

## Diagnostic commands

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli status
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli health
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli queue
```

`queue` is read-only: it connects to DEV and PROD independently and reports their queues.

## Server commands

No server is modified implicitly.

Examples:

```powershell
# DEV backend, Symfony dev
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli server-start dev --env dev

# DEV backend, Symfony prod mode but DEV code/data
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli server-restart dev --env prod

# PROD is always prod
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli server-start prod --env prod
```

The command below must fail:

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m control_center.cli server-start prod --env dev
```

## Important

R2 does not delete the historical Worker from EZScore yet.
First validate this extracted infrastructure. Then R3 can remove server/scheduler responsibilities
from the old Worker and introduce the EZScore-owned `analysis/worker_entrypoint.py`.

NO PUSH is performed by this deliverable.
