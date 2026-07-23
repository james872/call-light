# Call Light

Call Light is a peer-to-peer visual call system for live musicians. Each
Station is a Raspberry Pi with a momentary button and LED; there is no master
controller. A press starts or clears the shared Call on every Station.

## Production deployment

The production image is the primary deployment method.

**Download the production image:** [ADD DOWNLOAD LINK HERE](ADD-PRODUCTION-IMAGE-DOWNLOAD-LINK)

### What you need

- A Raspberry Pi Zero W (or compatible Raspberry Pi)
- A **minimum 4 GB** microSD card
- A momentary pushbutton connected between BCM GPIO 17 and ground
- An LED and suitable current-limiting resistor connected to BCM GPIO 27
- 5 V USB power

### First-run deployment from the image

1. Flash the Call Light `1.0.0` production image to the microSD card.
2. Insert the card and power the Station.
3. The factory configuration uses the station name `default` and contains no
   saved Wi-Fi networks, so the Station enters setup mode automatically.
4. Connect a phone or computer to the open Wi-Fi network named
   `call-<last-six-hex-digits-of-the-wlan0-MAC>`.
5. Open [http://192.168.2.1:8080](http://192.168.2.1:8080).
6. Save the venue Wi-Fi network, set the station name, then reboot the
   Station. It joins the highest-priority saved Wi-Fi network that it finds.

Setup mode is indicated by three short LED flashes followed by a pause. Hold
the physical button for 10 seconds while in setup mode to leave it and restart
the Station.

The image must be built from the release tag, include the Call Light service,
and contain no saved NetworkManager Wi-Fi profiles. The first boot generates
the Station ID; no Internet access is needed for normal operation.

## Using the Web UI

Open the Station's IP address on port 8080 from a device on the same network.
The Web UI provides:

- Call/Clear control and live Station status
- Station list, peer health, and the latest 10 events
- Station name, LED brightness, and flash-rate settings
- Saved Wi-Fi networks, order, and current network details
- Setup mode and reboot controls
- Per-Station software update checks

Changing a Station name prompts for a reboot. Rebooting applies the configured
name to the Pi hostname and ensures subsequent event and peer messages use the
new name.

## Updates

Each Station checks GitHub for newer release tags. In the Web UI select
**Check for updates**, then **Update**. The Station is temporarily offline
while it installs the release and restarts automatically.

Release tags and the root `VERSION` file must match exactly. Never move an
already-pushed tag; create a new version tag for each release.

## Recovery or developer installation

If a Station has Internet access, install or repair it from a terminal with:

```bash
curl -fsSL https://raw.githubusercontent.com/james872/call-light/main/deploy/install-pi.sh | sudo bash
```

The installer deploys the newest release tag and restarts
`call-light.service`. Check the service and logs with:

```bash
systemctl status call-light.service
journalctl -u call-light.service -f
```

`deploy/firstrun.sh` remains available for Raspberry Pi Imager-based online
provisioning. It requires Wi-Fi and Internet access, so it is not used by the
offline-ready production image.

## Network behaviour

Stations use mDNS discovery and direct ZeroMQ messaging on the same Wi-Fi LAN.
Heartbeats repair missed events and identify offline peers. When Wi-Fi
reconnects, the Station re-registers discovery so the mesh can reform.

## License

MIT License
