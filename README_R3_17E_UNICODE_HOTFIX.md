# EZS_orchestrator R3.17E — Windows Unicode stdout hotfix

Live LAB execution proved that queue/claim/dispatch reach EZStudio_lab and start
the Python worker on the RTX 2060.

The permanent orchestrator then crashed while replaying captured child output:

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\ufffd'
```

Cause:
- child stdout is captured as UTF-8;
- invalid bytes may become U+FFFD;
- Windows service stdout is CP1252;
- plain `print(proc.stdout)` may therefore crash the permanent service.

R3.17E keeps the captured attempt logs in UTF-8 and only sanitizes the console
replay with `backslashreplace`.

No change to:
- target routing;
- DEV/PROD/LAB queues;
- GPU singleton;
- planner;
- transports;
- lifecycle;
- deployment;
- business analysis.

## Apply

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_LAB_R3_17E_UNICODE_HOTFIX.zip" `
  -C H:\EZS_orchestrator `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-lab-r3_17e-unicode.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-lab-r3_17e-unicode.ps1
```

Then restart the permanent service once.
