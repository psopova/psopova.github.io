# Push the current state of the portfolio.
$ErrorActionPreference = "Continue"
git add -A 2>&1 | Out-Null
git commit -q -m "Serve the site from the repository root" 2>&1 | Out-Null
git push 2>&1 | ForEach-Object { if ($_ -notmatch 'warning: .*LF will be replaced') { $_ } }
if ($LASTEXITCODE -eq 0) {
  Write-Host ""
  Write-Host "Pushed. Site rebuilds in a minute: https://psopova.github.io/" -ForegroundColor Green
} else {
  Write-Host "Push failed, see above." -ForegroundColor Red
}
