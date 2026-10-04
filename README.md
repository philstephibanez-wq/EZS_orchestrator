# EZS_orchestrator — R3.10

Local orchestration layer for EZScore.

## Core rule

**DEV must never be able to break PROD.**

EZScore owns business logic. `EZS_orchestrator` owns execution, lifecycle, isolation,
scheduling and local administration.

## Physical topology

### DEV
- root: `H:\EZScore_dev`
- Symfony backend: `127.0.0.1:8602`
- public/local Caddy: `127.0.0.1:8502`
- analysis Python: `H:\EZScore_dev\.venv-py313\Scripts\python.exe`
- allowed `APP_ENV`: `dev|prod`

### PROD
- root: `H:\EZScore`
- Symfony backend: `127.0.0.1:8511`
- gateway: `127.0.0.1:8510`
- public Caddy: `127.0.0.1:8501`
- analysis Python: `H:\EZScore\.venv-py313\Scripts\python.exe`
- `APP_ENV=prod` only

Public chain:

```text
Cloudflare
→ Caddy PROD :8501
→ Gateway PROD :8510
→ Symfony PROD :8511
```

The public origin port `8501` is immutable.

## Architecture

```text
Job DEV
→ Scheduler
→ Executor
→ H:\EZScore_dev\analysis\worker_entrypoint.py

Job PROD
→ Scheduler
→ Executor
→ H:\EZScore\analysis\worker_entrypoint.py
```

The orchestrator contains no musical-analysis business logic.

Main modules:
- `control_center/`: local administration UI and CLI
- `server_manager/`: DEV/PROD Symfony lifecycle
- `gateway_manager/`: PROD gateway lifecycle
- `caddy_manager/`: isolated DEV/PROD reverse-proxy lifecycle
- `prod_lifecycle/`: protected PROD start/stop/restart/maintenance
- `scheduler/`: queue and resource arbitration
- `executor/`: target-owned analysis execution
- `service/`: permanent scheduler service
- `runtime_guard/`: lifecycle protection while analysis is active
- `contracts/`: neutral versioned contracts
- `config/`: machine-local topology
- `runtime/`: generated runtime state only
- `logs/`: generated logs only

## PROD lifecycle

Allowed PROD operations are deliberately limited to start, stop, restart,
maintenance ON/OFF and status. The Control Center must not expose arbitrary PROD
deployment, code editing, database mutation, storage mutation or business-analysis execution.

### CLI

```powershell
cd H:\EZS_orchestrator
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

& $Python -m control_center.cli status
& $Python -m control_center.cli prod-start
& $Python -m control_center.cli prod-restart
& $Python -m control_center.cli prod-stop
& $Python -m control_center.cli prod-maintenance-on
& $Python -m control_center.cli prod-maintenance-off
```

## Permanent service

```powershell
cd H:\EZS_orchestrator
$Python = "H:\Python\pythoncore-3.14-64\python.exe"

& $Python -m service.service_cli start --target dev --poll-seconds 2
& $Python -m service.service_cli status
```

## Control Center

```powershell
cd H:\EZS_orchestrator
powershell -ExecutionPolicy Bypass -File .\scripts\start_control_center.ps1
```

UI: `http://127.0.0.1:8700/`

## Caddy contract

```caddy
:8501 {
    bind 127.0.0.1
    reverse_proxy 127.0.0.1:8510
}
```

DEV remains isolated on `8502`.

## Gateway contract

Expected protocol: `ezscore.online-gateway.v3`

Status endpoint: `http://127.0.0.1:8510/__ezscore_gateway_status`

Maintenance mode intentionally returns HTTP 503 to public application requests.
A 503 during maintenance still proves that Caddy is alive; backend and gateway health
are checked independently.

## Tests

```powershell
cd H:\EZS_orchestrator
powershell -ExecutionPolicy Bypass -File .\bootstrap-r3_10.ps1
```

Validated baseline:

```text
53 tests OK
EZS_ORCHESTRATOR_R3_10_PROD_LIFECYCLE_OK
```

Live acceptance validated on 2026-10-04:
- full PROD restart restores `8511 + 8510 + 8501`
- start from fully stopped PROD restores all three listeners
- maintenance ON returns public HTTP 503
- maintenance OFF restores normal public traffic
- public endpoint returns HTTP 200 with non-empty content
- Symfony PROD runs without debug/profiler headers
- DEV lifecycle restart leaves all PROD listener PIDs unchanged

## Hard invariants

1. DEV never mutates `H:\EZScore`.
2. PROD never uses `H:\EZScore_dev`.
3. Cross-root execution is rejected.
4. PROD physical runtime is `APP_ENV=prod` only.
5. Analysis implementation always belongs to the selected EZScore checkout.
6. Scheduler contains no analysis business logic.
7. Executor uses target-owned Python and entrypoint.
8. One GPU slot is used until explicitly changed.
9. No silent fallback.
10. Runtime/log files are generated state and are not versioned.
