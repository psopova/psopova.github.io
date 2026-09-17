#!/usr/bin/env bash
# Usage:  ./setup-git.sh YOUR_GITHUB_USERNAME
set -e
U="${1:?Pass your GitHub username, e.g. ./setup-git.sh arminas}"
sed -i "s|GITHUB_URL|https://github.com/$U/rig-tooling-bench|" docs/index.html
git init -q
git add -A
git -c user.name="$U" -c user.email="$U@users.noreply.github.com" commit -qm "Rig Tooling Bench: two Blender add-ons and the benchmark rig"
git branch -M main
git remote add origin "https://github.com/$U/rig-tooling-bench.git"
echo "Done. Now run:  git push -u origin main"
echo "Then on github.com: Settings > Pages > Source: main, folder: /docs"
echo "Your site: https://$U.github.io/rig-tooling-bench/"
