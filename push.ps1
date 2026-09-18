# Push, switch GitHub Pages to the Actions workflow build, and report honestly.
$ErrorActionPreference = "Continue"
if (Test-Path ".git\index.lock") { Remove-Item -Force ".git\index.lock" }

git add -A 2>&1 | Out-Null
git commit -q -m "Deploy via GitHub Actions instead of the legacy Jekyll builder" 2>&1 | Out-Null
git push 2>&1 | ForEach-Object { if ($_ -notmatch 'warning: .*LF will be replaced') { $_ } }
if ($LASTEXITCODE -ne 0) { Write-Host "Push failed, see above." -ForegroundColor Red; exit 1 }
Write-Host "Pushed." -ForegroundColor Green

Write-Host "Switching Pages to the workflow build..."
gh api -X PUT repos/psopova/psopova.github.io/pages -f "build_type=workflow" *> $null
$src = gh api repos/psopova/psopova.github.io/pages --jq "{build_type,status}" 2>$null
Write-Host "  now: $src"

Write-Host ""
Write-Host "Watching the deploy (about a minute)..." -ForegroundColor Cyan
Start-Sleep -Seconds 12
gh run list --workflow="Deploy site" --limit 1
Write-Host ""
Write-Host "Follow it live with:  gh run watch"
Write-Host "If it fails:          gh run view --log-failed | Select-Object -Last 30"
Write-Host "Site: https://psopova.github.io/"
