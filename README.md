# Call Light

A distributed Raspberry Pi based call-light system for live musicians.

The project provides a simple, reliable visual indication that any performer on stage can trigger with a momentary pushbutton.

Every station is identical.

There is **no master controller**.

Each node automatically discovers every other node on the local network and communicates using peer-to-peer messaging.

---

## Features

- Raspberry Pi Zero W compatible
- Raspberry Pi OS Lite
- Peer-to-peer architecture
- No central server
- Automatic node discovery using mDNS (Zeroconf)
- Full-mesh messaging (every station talks directly to every peer)
- Versioned call state with automatic convergence via heartbeats
- Protocol version checking (incompatible peers are flagged, not silently broken)
- GPIO pushbutton input
- GPIO LED output
- Flask web interface with live status, peer health, and a virtual call button
- Per-station settings from the web UI: station name (synced to the machine hostname), flash rate, LED brightness
- Time-stamped event log of calls and clears, including originating station
- Per-station update button in the web UI (pulls the latest GitHub release)
- Heartbeats
- Automatic installation
- systemd service
- GitHub-based deployment
- Headless installation using Raspberry Pi Imager

---

## Hardware

Each node requires

- Raspberry Pi Zero W
- MicroSD card
- Momentary pushbutton
- LED
- Current limiting resistor
- 5V USB power

---

## Network

Nodes communicate over WiFi.

No Internet access is required after installation.

Discovery is performed using mDNS.

Messaging is performed using ZeroMQ.

---

## Project Status

Current Version

0.1.0

Current Milestone

Bootstrap

---

## Roadmap

- Bootstrap
- Web UI
- Discovery
- Messaging
- GPIO
- Diagnostics
- Release 1.0

---

## Installation

Deployment is designed for Raspberry Pi Imager.

1. Flash Raspberry Pi OS Lite.
2. Configure hostname and WiFi.
3. Configure the first-boot script.
4. Boot the Pi.
5. Installation completes automatically.

The first-boot script clones this repository, checks out the newest
release tag, installs dependencies, generates the station's identity,
and installs the systemd service. Internet access is required during
installation only.

### Install on an already-booted Raspberry Pi

Connect the Pi to WiFi, then run the following command in its terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/james872/call-light/main/deploy/install-pi.sh | sudo bash
```

The installer is safe to run again. It installs Git and Python, clones or
updates `/opt/call-light`, creates its Python environment, preserves an
existing station configuration, and starts the `call-light` systemd service.
It deploys the newest release tag; while there are no release tags it deploys
`main` so the project can be tested. To explicitly test a branch, tag, or
commit, run `sudo CALL_LIGHT_REF=your-ref ./deploy/install-pi.sh`.

If you have already cloned the repository, run `sudo ./deploy/install-pi.sh`
from that checkout instead.

After it finishes, open `http://<pi-ip-address>:8080` from a device on the
same WiFi. Check the service with `systemctl status call-light.service` and
view its live logs with `journalctl -u call-light.service -f`.

---

## Updates

Each station's web UI shows when a newer release is available
(internet permitting). The Update button updates that station only:
fetch, check out the newest release tag, reinstall dependencies,
restart the service.

Stations running an older protocol version appear on their peers as
"incompatible — update required", so partial upgrades are visible
rather than silently broken.

---

## License

MIT License
