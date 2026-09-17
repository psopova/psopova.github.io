# Publishes the portfolio to GitHub Pages.
#   powershell -ExecutionPolicy Bypass -File .\publish.ps1
# Native commands write progress to stderr, so we check exit codes instead of trapping.
$ErrorActionPreference = "Continue"

function Fail($m) { Write-Host $m -ForegroundColor Red; exit 1 }

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Fail "GitHub CLI not found. Run: winget install --id GitHub.cli -e   then reopen PowerShell."
}
gh auth status *> $null
if ($LASTEXITCODE -ne 0) { Fail "Not signed in. Run: gh auth login" }

$U    = (gh api user --jq .login).Trim()
if (-not $U) { Fail "Could not read your GitHub username." }
$REPO = "$U.github.io"
$SITE = "https://$U.github.io/"
Write-Host ""
Write-Host "GitHub user : $U"    -ForegroundColor Cyan
Write-Host "Repository  : $REPO" -ForegroundColor Cyan
Write-Host "Site        : $SITE" -ForegroundColor Cyan
Write-Host ""

# stamp the real URLs into the page and the readme
$idx  = "docs\index.html"
$html = Get-Content $idx -Raw
$html = $html -replace 'GITHUB_URL', "https://github.com/$U/$REPO"
$html = $html -replace 'https://github\.com/(zemis|psopova)/rig-tooling-bench', "https://github.com/$U/$REPO"
Set-Content $idx $html -NoNewline -Encoding UTF8

$rd = Get-Content "README.md" -Raw
$rd = $rd -replace 'GITHUB_PAGES_URL', $SITE
Set-Content "README.md" $rd -NoNewline -Encoding UTF8
Write-Host "URLs stamped into the page and readme."

if (-not (Test-Path ".git")) { git init -q }
if (-not (git config user.name))  { git config user.name  $U }
if (-not (git config user.email)) { git config user.email "$U@users.noreply.github.com" }

git add -A 2>&1 | Out-Null
git commit -q -m "Portfolio: Blender add-ons for rigged characters" 2>&1 | Out-Null
git branch -M main
Write-Host "Committed."

# does the repo exist yet?
gh repo view "$U/$REPO" *> $null
if ($LASTEXITCODE -eq 0) {
  Write-Host "Repository already exists, reusing it."
} else {
  Write-Host "Creating repository $REPO ..."
  gh repo create $REPO --public --description "Blender add-ons for rigged characters, built and benchmarked headlessly" *> $null
  if ($LASTEXITCODE -ne 0) { Fail "Could not create the repository. Create it manually at github.com/new named $REPO, then run this script again." }
  Write-Host "Created."
}

git remote remove origin *> $null
git remote add origin "https://github.com/$U/$REPO.git"
Write-Host "Pushing..."
git push -u origin main 2>&1 | ForEach-Object { if ($_ -notmatch 'warning: .*LF will be replaced') { $_ } }
if ($LASTEXITCODE -ne 0) { Fail "Push failed. Paste the output above." }

Write-Host ""
Write-Host "Turning on GitHub Pages..."
gh api -X POST "repos/$U/$REPO/pages" -f "source[branch]=main" -f "source[path]=/docs" *> $null
if ($LASTEXITCODE -eq 0) { Write-Host "Pages enabled." -ForegroundColor Green }
else { Write-Host "Could not enable Pages automatically. Do it at: https://github.com/$U/$REPO/settings/pages  (Branch: main, folder: /docs)" -ForegroundColor Yellow }

Write-Host ""
Write-Host "DONE." -ForegroundColor Green
Write-Host "Site (live in a minute or two): $SITE"
Write-Host "Repo: https://github.com/$U/$REPO"
