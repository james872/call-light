#!/bin/bash
#
# Call Light per-station updater.
#
# Launched detached by the web UI's Update button. Checks out the
# newest release tag, reinstalls dependencies and restarts the
# service. This station only - see ADR 0002.
#

set -euo pipefail

cd "$(dirname "$0")/.."

git fetch --tags --quiet

LATEST="$(git tag --sort=-v:refname | head -n 1)"

if [ -z "${LATEST}" ]; then
    echo "No release tags found; nothing to update to."
    exit 0
fi

echo "Updating to ${LATEST}"

git checkout --quiet "${LATEST}"

# Keep update installs consistent with first-boot installs. gpiozero uses the
# Raspberry Pi OS lgpio package to access the physical GPIO header.
apt-get update
apt-get install -y python3-lgpio
sed -i 's/^include-system-site-packages = false$/include-system-site-packages = true/' venv/pyvenv.cfg

venv/bin/pip install -r requirements.txt --prefer-binary --retries 10 --timeout 60

#
# Give the HTTP response that triggered us a moment to be
# delivered before the service dies.
#

sleep 1

systemctl restart call-light
