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

set_default_hostname() {
    local interface="wlan0"
    local mac_file="/sys/class/net/${interface}/address"
    local mac
    local suffix
    local hostname

    if [ ! -r "${mac_file}" ]; then
        echo "Call Light: Wi-Fi interface ${interface} was not found." >&2
        exit 1
    fi

    mac="$(tr -d ':' < "${mac_file}")"

    if [[ ! "${mac}" =~ ^[[:xdigit:]]{12}$ ]]; then
        echo "Call Light: invalid MAC address for ${interface}: ${mac}" >&2
        exit 1
    fi

    suffix="${mac: -6}"
    hostname="call-${suffix,,}"

    # The marker prevents a re-run from overwriting a name chosen in the UI.
    if [ -e /etc/call-light/initial-hostname ]; then
        return
    fi

    echo "Call Light: setting initial hostname to ${hostname}"

    if ! hostnamectl set-hostname "${hostname}"; then
        printf '%s\n' "${hostname}" > /etc/hostname
        hostname "${hostname}"
    fi

    printf '%s\n' "${hostname}" > /etc/call-light/initial-hostname
}

echo "Call Light: installing system packages"
apt-get update
# gpiozero needs a pin factory to access the physical header.  Raspberry Pi OS
# supplies lgpio as a system package, so the virtual environment below is
# deliberately allowed to see system site packages.
apt-get install -y git python3-venv python3-pip python3-lgpio

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
python3 -m venv --system-site-packages "${TARGET}/venv"
"${TARGET}/venv/bin/pip" install --upgrade pip --retries 10 --timeout 60
"${TARGET}/venv/bin/pip" install -r "${TARGET}/requirements.txt" --prefer-binary --retries 10 --timeout 60

mkdir -p /etc/call-light

set_default_hostname

if [ ! -f /etc/call-light/config.yaml ]; then
    cp "${TARGET}/config/config.example.yaml" /etc/call-light/config.yaml
fi

install -m 0644 "${TARGET}/deploy/call-light.service" /etc/systemd/system/call-light.service
systemctl daemon-reload
systemctl enable --now call-light.service

echo
echo "Call Light is running. Open http://$(hostname -I | awk '{print $1}'):8080"
echo "Status: systemctl status call-light.service"
