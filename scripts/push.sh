#!/usr/bin/env bash
set -euo pipefail

msg="${*:-Atualização $(date '+%Y-%m-%d %H:%M')}"

git status -sb
git add -A

if git diff --cached --quiet; then
  echo "Nada para commitar."
  exit 0
fi

git commit -m "$msg"
git push
