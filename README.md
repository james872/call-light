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
- UUID-based messaging
- Automatic duplicate suppression
- Recursive message retransmission
- GPIO pushbutton input
- GPIO LED output
- Lightweight Flask web interface
- Event logging
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

---

## License

MIT License