"""
ZeroMQ full-mesh messaging.

Every station binds one PUB socket and connects a SUB socket to
every discovered peer. There is no relaying and no duplicate
suppression - on a single LAN every station hears every other
station directly. See ADR 0001.

Wire format: one JSON object per message.

    {
        "protocol":      int   protocol version
        "type":          str   CALL | CLEAR | HEARTBEAT
        "station_id":    str   sender's Station ID
        "display_name":  str   sender's Display Name
        "state":         str   sender's current state
        "counter":       int   state version counter
        "state_origin":  str   station id that produced the state version
    }
"""

from __future__ import annotations

import json
import threading
import time

import zmq

from .constants import EVENT_CALL
from .constants import EVENT_CLEAR
from .constants import HEARTBEAT_INTERVAL_S
from .constants import MSG_HEARTBEAT
from .constants import PROTOCOL_VERSION


class Messaging:
    """
    The messaging layer for one station.
    """

    def __init__(self, calllight) -> None:

        self.app = calllight

        self.context = zmq.Context.instance()

        self.pub = self.context.socket(zmq.PUB)

        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, b"")

        #
        # Endpoints we have already connected to.
        #

        self.endpoints: set[str] = set()

    def start(self) -> None:
        """
        Bind the PUB socket and start the receive and heartbeat loops.
        """

        port = self.app.config.messaging_port

        self.pub.bind("tcp://*:%d" % port)

        self.app.transport = self

        threading.Thread(
            target=self._receive_loop,
            name="messaging-receive",
            daemon=True,
        ).start()

        threading.Thread(
            target=self._heartbeat_loop,
            name="messaging-heartbeat",
            daemon=True,
        ).start()

        self.app.logger.info("Messaging started on port %d", port)

    def connect_peer(self, address: str, port: int) -> None:
        """
        Connect the SUB socket to a newly discovered peer.

        ZeroMQ handles reconnection automatically, so a peer that
        reboots does not need rediscovery here.
        """

        endpoint = "tcp://%s:%d" % (address, port)

        if endpoint in self.endpoints:
            return

        self.endpoints.add(endpoint)

        self.sub.connect(endpoint)

        self.app.logger.info("Connected to peer at %s", endpoint)

    #
    # Sending
    #

    def _message(self, msg_type: str) -> dict:

        with self.app.lock:

            return {

                "protocol": PROTOCOL_VERSION,
                "type": msg_type,
                "station_id": self.app.station_id,
                "display_name": self.app.display_name,
                "state": self.app.state,
                "counter": self.app.state_counter,
                "state_origin": self.app.state_origin,

            }

    def _send(self, message: dict) -> None:

        self.pub.send_string(json.dumps(message))

    def broadcast_event(self, event_type: str) -> None:
        """
        Broadcast a locally generated CALL or CLEAR event.
        """

        self._send(self._message(event_type))

    def _heartbeat_loop(self) -> None:

        while self.app.running:

            self._send(self._message(MSG_HEARTBEAT))

            time.sleep(HEARTBEAT_INTERVAL_S)

    #
    # Receiving
    #

    def _receive_loop(self) -> None:

        poller = zmq.Poller()
        poller.register(self.sub, zmq.POLLIN)

        while self.app.running:

            if not poller.poll(timeout=500):
                continue

            try:

                message = json.loads(self.sub.recv_string())

                self._handle(message)

            except (ValueError, KeyError) as error:

                self.app.logger.warning(
                    "Ignoring malformed message: %s", error
                )

    def _handle(self, message: dict) -> None:

        station_id = message["station_id"]

        #
        # Our own messages can arrive if discovery ever connects
        # us to ourselves. Ignore them.
        #

        if station_id == self.app.station_id:
            return

        protocol = message["protocol"]

        if protocol != PROTOCOL_VERSION:

            #
            # Incompatible peer: record that we saw it (so the web
            # UI can flag it) but ignore the content entirely.
            #

            self.app.record_peer(
                station_id,
                display_name=message.get("display_name", station_id[:8]),
                last_seen=time.monotonic(),
                protocol_version=protocol,
            )

            return

        self.app.record_peer(
            station_id,
            display_name=message["display_name"],
            last_seen=time.monotonic(),
            protocol_version=protocol,
            state=message["state"],
        )

        msg_type = message["type"]

        if msg_type in (EVENT_CALL, EVENT_CLEAR):

            self.app.apply_event(
                msg_type,
                message["counter"],
                message["state_origin"],
                message["display_name"],
            )

        elif msg_type == MSG_HEARTBEAT:

            self.app.apply_heartbeat_state(
                message["state"],
                message["counter"],
                message["state_origin"],
                station_id,
                message["display_name"],
            )
