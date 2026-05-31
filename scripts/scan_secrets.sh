#!/usr/bin/env sh
set -eu

if rg -n --hidden \
  -g '!.git/**' \
  -g '!artifacts/**' \
  -g '!build/**' \
  -g '!dist/**' \
  -g '!*.egg-info/**' \
  -g '!.pytest_cache/**' \
  -g '!data/demo/*.sqlite3*' \
  -g '!scripts/scan_secrets.sh' \
  -e '([A-Z0-9_]*(API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|AUTHORIZATION)[A-Z0-9_]*\s*=\s*.+)' \
  -e '(DATABASE_URL\s*=\s*.+)' \
  -e '(PRIVATE KEY|BEGIN RSA|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,})' \
  .; then
  printf '%s\n' "Potential secret-like values found. Review the matches above before committing."
  exit 1
fi

printf '%s\n' "No secret-like values found."
