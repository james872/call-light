"""NetworkManager-backed Wi-Fi status and connection management."""

from __future__ import annotations

import ipaddress
from pathlib import Path
import shutil
import subprocess


class NetworkManager:
    """Small, defensive wrapper around ``nmcli`` for the station Web UI."""

    def __init__(self, logger) -> None:
        self.logger = logger

    def _run(self, *args: str) -> str:
        if shutil.which("nmcli") is None:
            raise RuntimeError("NetworkManager (nmcli) is not installed")
        result = subprocess.run(
            ["nmcli", "-g", *args], capture_output=True, text=True,
            timeout=20, check=True,
        )
        return result.stdout.strip()

    def _wifi_device(self) -> str:
        for line in self._run("DEVICE,TYPE", "device", "status").splitlines():
            device, _, kind = line.rpartition(":")
            if kind == "wifi":
                return device
        raise RuntimeError("No Wi-Fi device was found")

    def snapshot(self) -> dict:
        """Return Wi-Fi profiles and the active connection's IPv4 details."""
        try:
            device = self._wifi_device()
            known = []
            profiles = self._run("NAME,UUID,TYPE", "connection", "show")
            active_uuid = self._run("GENERAL.CON-UUID", "device", "show", device)
            for line in profiles.splitlines():
                name, uuid, kind = line.rsplit(":", 2)
                if kind == "802-11-wireless":
                    known.append({"ssid": name, "uuid": uuid, "active": uuid == active_uuid})
            raw_address = self._run("IP4.ADDRESS", "device", "show", device)
            address = raw_address.split("/", 1)[0] if raw_address else None
            prefix = raw_address.split("/", 1)[1] if "/" in raw_address else None
            subnet = None if not address or not prefix else str(
                ipaddress.ip_interface("%s/%s" % (address, prefix)).network
            )
            return {"available": True, "device": device, "current": {
                "ssid": next((item["ssid"] for item in known if item["active"]), None),
                "ip_address": address,
                "gateway": self._run("IP4.GATEWAY", "device", "show", device) or None,
                "subnet": subnet,
            }, "known": sorted(known, key=lambda item: item["ssid"].lower())}
        except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as error:
            self.logger.warning("Could not read Wi-Fi status: %s", error)
            return {"available": False, "error": str(error), "current": {}, "known": []}

    def connect(self, ssid: str, password: str | None) -> None:
        ssid = "" if ssid is None else str(ssid).strip()
        if not ssid or len(ssid) > 32:
            raise ValueError("Wi-Fi name must be between 1 and 32 characters")
        if password is not None and password and not 8 <= len(password) <= 63:
            raise ValueError("Wi-Fi password must be 8 to 63 characters")
        command = ["nmcli", "device", "wifi", "connect", ssid, "ifname", self._wifi_device()]
        if password:
            command.extend(["password", password])
        subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)

    def delete(self, uuid: str) -> None:
        uuid = str(uuid).strip()
        if not uuid:
            raise ValueError("Missing Wi-Fi profile identifier")
        subprocess.run(["nmcli", "connection", "delete", "uuid", uuid],
                       capture_output=True, text=True, timeout=30, check=True)

    def setup_ssid(self) -> str:
        """Return the stable setup-network name derived from wlan0's MAC."""
        try:
            mac = Path("/sys/class/net/wlan0/address").read_text().strip()
        except OSError as error:
            raise RuntimeError("Could not read the Wi-Fi MAC address") from error
        suffix = mac.replace(":", "").lower()
        if len(suffix) != 12 or not all(char in "0123456789abcdef" for char in suffix):
            raise RuntimeError("Wi-Fi MAC address is invalid")
        return "call-%s" % suffix[-6:]

    def start_setup_hotspot(self) -> str:
        """Start an open AP with DHCP on the fixed setup subnet.

        ``ipv4.method shared`` makes NetworkManager run DHCP and NAT. The
        static address makes the setup UI predictable without discovery.
        """
        device = self._wifi_device()
        ssid = self.setup_ssid()
        name = "call-light-setup"

        subprocess.run(
            ["nmcli", "connection", "delete", "id", name],
            capture_output=True, text=True, timeout=30,
        )
        subprocess.run(
            ["nmcli", "connection", "add", "type", "wifi", "ifname", device,
             "con-name", name, "ssid", ssid],
            capture_output=True, text=True, timeout=30, check=True,
        )
        subprocess.run(
            ["nmcli", "connection", "modify", name,
             "802-11-wireless.mode", "ap",
             "802-11-wireless.band", "bg",
             "802-11-wireless-security.key-mgmt", "none",
             "ipv4.method", "shared",
             "ipv4.addresses", "192.168.2.1/24",
             "ipv6.method", "disabled",
             "connection.autoconnect", "no"],
            capture_output=True, text=True, timeout=30, check=True,
        )
        subprocess.run(
            ["nmcli", "connection", "up", "id", name],
            capture_output=True, text=True, timeout=60, check=True,
        )
        return ssid
