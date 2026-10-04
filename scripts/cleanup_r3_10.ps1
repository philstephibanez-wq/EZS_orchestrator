param(
    [string]$Root = "H:\EZS_orchestrator"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $Root ".git"))) {
    throw "Not a git checkout: $Root"
}

Set-Location $Root

$obsolete = @(
    "README-R3.10a.md",
    "README-R3.10b.md"
)

foreach ($file in $obsolete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "removed $file"
    }
}

Write-Host ""
Write-Host "=== VALIDATION ==="
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed"
}

Write-Host ""
Write-Host "=== GIT STATUS ==="
git status --short

Write-Host ""
Write-Host "Cleanup complete. Review git diff before commit/push."
