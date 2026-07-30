#!/usr/bin/env bash
#
# Pull the latest ESWS from GitHub and bring the stack up on it.
#
#   make update
#
# Rebuilds only when something that goes *into* the image changed. Application
# code is bind-mounted, so a pull that only touches Python needs the services
# restarted, not a fifteen-minute conda rebuild -- but it does need that restart,
# because a running server holds its modules in memory and will otherwise keep
# serving the code it started with.
#
# Env:
#   NO_RESTART=1   pull and rebuild but leave the running stack alone
set -euo pipefail
cd "$(dirname "$0")/.."

# A rebuild against uncommitted work, or a pull that cannot apply cleanly, is a
# worse outcome than stopping here.
if [ -n "$(git status --porcelain)" ]; then
    echo "!! Uncommitted changes; commit or stash them first:" >&2
    git status --short >&2
    exit 1
fi

if ! git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' >/dev/null 2>&1; then
    echo "!! This branch tracks no upstream; nothing to pull from." >&2
    exit 1
fi

before="$(git rev-parse HEAD)"
echo ">> Fetching $(git rev-parse --abbrev-ref '@{upstream}')"
git fetch --quiet

incoming="$(git log --oneline "${before}..@{upstream}")"
if [ -z "${incoming}" ]; then
    echo ">> Already up to date at $(git rev-parse --short HEAD)"
    exit 0
fi

echo ">> Incoming:"
echo "${incoming}" | sed 's/^/   /'

# --ff-only: never leave the tree mid-merge on someone's server.
git merge --ff-only '@{upstream}'
echo ">> Now at $(git rev-parse --short HEAD)"

changed="$(git diff --name-only "${before}" HEAD)"

if [ "${NO_RESTART:-0}" = "1" ]; then
    echo ">> NO_RESTART set; leaving the stack as it is"
    exit 0
fi

# Only these end up baked into an image. Everything else is mounted at run time.
if echo "${changed}" | grep -qE '^(docker/|requirements/|docker-compose\.yml)'; then
    echo ">> Image inputs changed; rebuilding"
    docker compose build
fi

echo ">> Starting"
docker compose up -d

# Restart the services that run application code even when nothing was rebuilt:
# compose leaves an already-running container alone, and its Python has the old
# modules loaded.
if echo "${changed}" | grep -qE '^(tools/|scripts/)'; then
    echo ">> Application code changed; restarting wps and dashboard"
    docker compose restart wps dashboard
fi

echo ">> Updated. Check it with: make smoke"
