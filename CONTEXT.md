# Call Light

A distributed, peer-to-peer call-light system for live musicians. Identical Raspberry Pi stations discover each other on the local network; any performer can raise a visual signal seen by everyone on stage.

## Language

**Call**:
The single system-wide latched signal. While a Call is active, every Station flashes its light. There is at most one Call at a time; a Call has no target, and while events record which Station originated them, origin confers no special rights.
_Avoid_: alert, signal, page

**Event Log**:
A per-Station, time-stamped record of the Call and Clear events that Station saw, including each event's origin. It is a local view — logs are never merged across Stations — and timestamps are best-effort wall-clock time.
_Avoid_: history, audit trail

**Clear**:
The act of ending the active Call. Any press on any Station clears it — the button is a global toggle (press while idle starts a Call, press while active Clears it).
_Avoid_: cancel, acknowledge, dismiss

**Station**:
One physical unit — a Raspberry Pi with a button and a light. All Stations are identical; there is no master.
_Avoid_: node (in prose), controller, client

**Peer**:
Another Station as seen from a given Station over the network.

**Press**:
A performer's toggle action, regardless of source — the hardware button and the web UI button are the same gesture. A Press is interpreted against the Station's local state: it becomes a CALL if idle, a Clear if a Call is active.
_Avoid_: click, tap, trigger (as distinct actions)

**Station ID**:
The UUID generated on a Station's first boot and persisted locally. The protocol identifies Stations only by Station ID; hostname plays no protocol role.
_Avoid_: hostname (as identity), node id

**Display Name**:
The human-facing label for a Station (e.g. "Drums"), shown in the web UI. Never used by the protocol. Renaming a Station sets its Display Name and also updates the machine hostname to a sanitized form of it, so the network address matches the label.
_Avoid_: hostname (as label)

**Heartbeat**:
A periodic message a Station sends to all Peers announcing that it is alive and carrying its current view of the Call state, so Stations that missed an event converge.

**Idle / Calling**:
The two states a Station can be in: Idle (no active Call, light off) and Calling (a Call is active, light flashing). The light strictly mirrors this state and shows nothing else.
_Avoid_: on/off, alerting

**Incompatible**:
The status of a Peer speaking a different protocol version. Its messages are ignored, but it stays visible in the web UI as needing an update.

**Offline**:
The status of a Peer whose Heartbeats have stopped arriving. Offline Peers remain visible (marked, with last-seen time) rather than vanishing. Discovery (mDNS) never determines liveness; only Heartbeats do.
_Avoid_: dead, dropped, removed
