# Explicit CALL/CLEAR events over a full mesh, with versioned-state repair via heartbeats

A Call is a single latched system-wide signal that any Station's button press toggles. Sending a raw TOGGLE on the wire makes near-simultaneous presses cancel each other (two people who both meant "start a Call" would blip the light off), so the pressing Station interprets the toggle locally and sends an explicit CALL or CLEAR event — simultaneous CALLs are idempotent. Because events can be missed (WiFi dropout, mid-Call boot), every state change carries a version (monotonic counter, origin UUID as tiebreak) and Heartbeats carry the sender's (state, version); a Station seeing a newer version adopts it, guaranteeing convergence within one heartbeat interval.

All Stations sit on one WiFi LAN and discover each other via mDNS, so every Station connects directly to every Peer (full mesh). The flood/relay design originally described in the README (recursive retransmission with UUID duplicate suppression) was dropped: relaying only pays off when two stations can reach a third but not each other, which does not occur on a single access point, and it costs a message-ID cache, loop suppression, and N× traffic.

## Considered Options

- **Raw TOGGLE events** — simplest message, but simultaneous presses cancel and any lost message permanently inverts a station's state. Rejected.
- **Flood/relay with dedupe** — resilience only for multi-AP topologies that aren't a target; complexity not earned. Rejected.
- **Pure periodic state broadcast (no events)** — robust but press→light latency bounded by the broadcast interval. Rejected as primary mechanism; retained in diluted form as heartbeat repair.
- **Formal CRDT/anti-entropy gossip** — provably convergent, massive overkill for one boolean across ~6 devices. Rejected.
