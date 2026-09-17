# Publishes the portfolio to GitHub Pages.
# Run from this folder:   powershell -ExecutionPolicy Bypass -File .\publish.ps1
$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Host "GitHub CLI not found." -ForegroundColor Red
  Write-Host "Run this, then close and reopen PowerShell:"
  Write-Host "  winget install --id GitHub.cli -e"
  exit 1
}
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "GitHub CLI is not signed in." -ForegroundColor Red
  Write-Host "Run:  gh auth login    (GitHub.com -> HTTPS -> Yes -> Login with a web browser)"
  exit 1
}

$U    = (gh api user --jq .login).Trim()
$REPO = "$U.github.io"
$SITE = "https://$U.github.io/"
Write-Host ""
Write-Host "GitHub user : $U"     -ForegroundColor Cyan
Write-Host "Repository  : $REPO"  -ForegroundColor Cyan
Write-Host "Site        : $SITE"  -ForegroundColor Cyan
Write-Host ""

# stamp the real URLs into the page and the readme
$idx = "docs\index.html"
$html = Get-Content $idx -Raw
$html = $html -replace 'GITHUB_URL', "https://github.com/$U/$REPO"
$html = $html -replace 'https://github\.com/(zemis|psopova)/[^"]*', "https://github.com/$U/$REPO"
Set-Content $idx $html -NoNewline -Encoding UTF8

$rd = Get-Content "README.md" -Raw
$rd = $rd -replace 'GITHUB_PAGES_URL', $SITE
Set-Content "README.md" $rd -NoNewline -Encoding UTF8

if (-not (Test-Path ".git")) { git init -q }
if (-not (git config user.name))  { git config user.name  $U }
if (-not (git config user.email)) { git config user.email "$U@users.noreply.github.com" }

git add -A
git commit -q -m "Portfolio: Blender add-ons for rigged characters" 2>&1 | Out-Null
git branch -M main

gh repo view "$U/$REPO" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
  Write-Host "Repository already exists, reusing it."
} else {
  gh repo create $REPO --public --description "Blender add-ons for rigged characters, built and benchmarked headlessly" --disable-wiki
}

git remote remove origin 2>&1 | Out-Null
git remote add origin "https://github.com/$U/$REPO.git"
git push -u origin main

Write-Host ""
Write-Host "Turning on GitHub Pages..."
gh api -X POST "repos/$U/$REPO/pages" -f "source[branch]=main" -f "source[path]=/docs" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "Pages enabled." -ForegroundColor Green }
else { Write-Host "Enable manually: Settings > Pages > Branch main, folder /docs" -ForegroundColor Yellow }

Write-Host ""
Write-Host "DONE." -ForegroundColor Green
Write-Host "Site (live in a minute or two): $SITE"
Write-Host "Repo: https://github.com/$U/$REPO"
