#!/usr/bin/env bash
# Creates the repo, wires it up and publishes the site.
# Needs GitHub CLI:  winget install --id GitHub.cli -e   then   gh auth login
set -e

command -v gh >/dev/null || { echo "GitHub CLI not found. Run: winget install --id GitHub.cli -e"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Not signed in. Run: gh auth login"; exit 1; }

U=$(gh api user --jq .login)
REPO="$U.github.io"
SITE="https://$U.github.io/"
echo "GitHub user : $U"
echo "Repository  : $REPO"
echo "Site        : $SITE"
echo

# stamp the real URLs into the page and the readme
sed -i "s|GITHUB_URL|https://github.com/$U/$REPO|g" index.html
sed -i "s|https://github.com/zemis/[^\"]*|https://github.com/$U/$REPO|g" index.html
sed -i "s|https://github.com/psopova/[^\"]*|https://github.com/$U/$REPO|g" index.html
sed -i "s|GITHUB_PAGES_URL|$SITE|g" README.md

git init -q 2>/dev/null || true
git config user.name  >/dev/null 2>&1 || git config user.name  "$U"
git config user.email >/dev/null 2>&1 || git config user.email "$U@users.noreply.github.com"
git add -A
git commit -qm "Portfolio: Blender add-ons for rigged characters" || echo "(nothing new to commit)"
git branch -M main

if gh repo view "$U/$REPO" >/dev/null 2>&1; then
  echo "Repository already exists, reusing it."
else
  gh repo create "$REPO" --public --description "Blender add-ons for rigged characters, built and benchmarked headlessly" --disable-wiki
fi

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$U/$REPO.git"
git push -u origin main

echo
echo "Turning on GitHub Pages..."
gh api -X POST "repos/$U/$REPO/pages" -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
  && echo "Pages enabled." \
  || echo "Pages not enabled automatically. Do it manually: Settings > Pages > Branch main, folder /docs"

echo
echo "DONE."
echo "Site (live in a minute or two): $SITE"
echo "Repo: https://github.com/$U/$REPO"
