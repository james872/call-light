#!/usr/bin/env bash
#
# Install or update one Call Light station on Raspberry Pi OS.
#
# Run this from a cloned checkout, or download it and set CALL_LIGHT_REPO.
# The script installs the service at /opt/call-light and is safe to re-run.
#
# Optional environment variables:
#   CALL_LIGHT_REPO=https://github.com/owner/call-light.git
#   CALL_LIGHT_REF=main             # branch, tag, or commit to deploy
#   CALL_LIGHT_TARGET=/opt/call-light

set -euo pipefail

REPO="${CALL_LIGHT_REPO:-https://github.com/james872/call-light.git}"
TARGET="${CALL_LIGHT_TARGET:-/opt/call-light}"
REF="${CALL_LIGHT_REF:-}"

if [ "${EUID}" -ne 0 ]; then
    exec sudo --preserve-env=CALL_LIGHT_REPO,CALL_LIGHT_REF,CALL_LIGHT_TARGET "$0" "$@"
fi

echo "Call Light: installing system packages"
apt-get update
apt-get install -y git python3-venv python3-pip

if [ -d "${TARGET}/.git" ]; then
    echo "Call Light: updating checkout in ${TARGET}"
    git -C "${TARGET}" remote set-url origin "${REPO}"
    git -C "${TARGET}" fetch --tags --prune origin
else
    if [ -e "${TARGET}" ]; then
        echo "Refusing to use ${TARGET}: it exists but is not a Git checkout." >&2
        exit 1
    fi

    echo "Call Light: cloning ${REPO}"
    git clone "${REPO}" "${TARGET}"
    git -C "${TARGET}" fetch --tags --prune origin
fi

# Production deployments follow the release-tag policy.  Until the first
# release tag exists, main is used so a new project can be tested on hardware.
if [ -z "${REF}" ]; then
    REF="$(git -C "${TARGET}" tag --sort=-v:refname | head -n 1)"
    REF="${REF:-main}"
fi

echo "Call Light: checking out ${REF}"
git -C "${TARGET}" checkout --quiet --force "${REF}"

echo "Call Light: installing Python dependencies"
python3 -m venv "${TARGET}/venv"
"${TARGET}/venv/bin/pip" install --upgrade pip --quiet
"${TARGET}/venv/bin/pip" install -r "${TARGET}/requirements.txt" --quiet

mkdir -p /etc/call-light
if [ ! -f /etc/call-light/config.yaml ]; then
    cp "${TARGET}/config/config.example.yaml" /etc/call-light/config.yaml
fi

install -m 0644 "${TARGET}/deploy/call-light.service" /etc/systemd/system/call-light.service
systemctl daemon-reload
systemctl enable --now call-light.service

echo
echo "Call Light is running. Open http://$(hostname -I | awk '{print $1}'):8080"
echo "Status: systemctl status call-light.service"
