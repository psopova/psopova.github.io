# Push the post-audit corrections, then point Pages at the repo root.
$ErrorActionPreference = "Continue"
if (Test-Path ".git\index.lock") { Remove-Item -Force ".git\index.lock" }
git add -A 2>&1 | Out-Null
git commit -q -m "Post-audit corrections: retract Shape Key Transfer, fix LOD error metric 17x, qualify weight claims, add failing assertions" 2>&1 | Out-Null
git push 2>&1 | ForEach-Object { if ($_ -notmatch 'warning: .*LF will be replaced') { $_ } }
if ($LASTEXITCODE -ne 0) { Write-Host "Push failed, see above." -ForegroundColor Red; exit 1 }
Write-Host ""
Write-Host "Pushed." -ForegroundColor Green
Write-Host "Pointing GitHub Pages at the repository root..."
gh api -X PUT repos/psopova/psopova.github.io/pages -f "source[branch]=main" -f "source[path]=/" *> $null
if ($LASTEXITCODE -eq 0) { Write-Host "Pages source set to /." -ForegroundColor Green }
else { Write-Host "Could not set it. Do it here: https://github.com/psopova/psopova.github.io/settings/pages  (Branch main, folder / root)" -ForegroundColor Yellow }
Write-Host ""
Write-Host "Site rebuilds in a minute or two: https://psopova.github.io/"
