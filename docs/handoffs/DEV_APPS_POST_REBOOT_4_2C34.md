# 4.2c34 — DEV FastCGI post-reboot recovery

Observed Windows (2026-10-29): v4.2c33 START clears obsolete root Caddy state and starts 8790/8791, then refuses EZS_DEV_APP_REFUSED_STALE_STATE for the old DEV FastCGI ownership state at runtime/v2-dev/app-backends.json.

New guard in the existing scripts/start.ps1: on invalid schema, refuse as before. On invalid attestation, clear stale state **only when both prior PIDs are nonexistent and both 8602/8862 TCP listeners are absent**. In mixed states or with any surviving process/listener, refuse unchanged. No foreign-process stop, no manual state deletion, no modification of PROD, LAB workers or jobs. Normal fresh start creates owned FastCGI pair and writes new state.

Required Windows gates: PHP contract test, PowerShell AST syntax, start on clean reboot state, verify 8502/8852 HTTP and LAB/Assistant readiness. When refusal persists inspect process owners and listeners rather than deleting state. START recovery is not a production PROD gateway restart; PROD remains separate.
