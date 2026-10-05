from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = (root/"scripts"/"start_control_center.ps1").read_text(encoding="utf-8-sig")

assert "-m control_center.web --port $Port --no-browser" in src
assert src.count("--no-browser") == 1

print("EZS_ORCHESTRATOR_V1_0_7_1_SINGLE_BROWSER_OK")
