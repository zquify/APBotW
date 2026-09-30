
"""Deliver Archipelago items to BotW through the WiiXLaunch TCP bridge.

This module is deliberately independent of ManualClient.py so it can be
tested and maintained without replacing the existing Archipelago client.
"""

import json
import logging
import socket
from pathlib import Path

log = logging.getLogger("BotWAP.Delivery")

BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8080
BRIDGE_TIMEOUT = 3.0

# AP item display name -> (BotW actor name, quantity)
#
# Only add mappings after verifying the actor name in-game.
ITEM_MAP = {
    "Hearty Durian": ("Item_Fruit_D", 1),
    "Apple": ("Item_Fruit_A", 1),
    "Royal Broadsword": ("Weapon_Sword_024", 1),
}

# Store delivery progress outside either source repository.
STATE_FILE = Path.home() / ".botw_ap_delivery.json"


class DeliveryError(Exception):
    """A delivery could not be safely completed."""


def send_to_bridge(actor_name, quantity=1):
    """Send one command and require an explicit bridge response."""
    if not actor_name or any(c.isspace() for c in actor_name):
        raise DeliveryError("Invalid BotW actor name")

    if not isinstance(quantity, int) or quantity < 1:
        raise DeliveryError("Quantity must be a positive integer")

    command = "GIVE {} {}\n".format(actor_name, quantity)

    try:
        with socket.create_connection(
            (BRIDGE_HOST, BRIDGE_PORT), timeout=BRIDGE_TIMEOUT
        ) as sock:
            sock.settimeout(BRIDGE_TIMEOUT)
            sock.sendall(command.encode("ascii"))

            response = bytearray()
            while not response.endswith(b"\n"):
                chunk = sock.recv(1)
                if not chunk:
                    break
                response.extend(chunk)

    except OSError as exc:
        raise DeliveryError("Bridge connection failed: {}".format(exc))

    if not response:
        raise DeliveryError("Bridge disconnected without a response")

    result = response.decode("ascii", errors="replace").strip()
    if result != "OK":
        raise DeliveryError("Bridge rejected command: {}".format(result))

    return True


def _load_state():
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}

    if not isinstance(state, dict):
        raise DeliveryError("Delivery state file is not a JSON object")

    return state


def _save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")

    temporary.replace(STATE_FILE)


class APItemDelivery:
    """Deliver newly received NetworkItems in their original AP order."""

    def __init__(self, slot_key):
        # Use a stable identifier for this AP server + slot.
        self.slot_key = slot_key
        self.state = _load_state()
        self.progress = self.state.setdefault(
            slot_key, {"next_index": 0}
        )

    @property
    def next_index(self):
        return int(self.progress.get("next_index", 0))

    def process(self, items_received, get_item_name):
        """Process items from next_index onward.

        items_received: ctx.items_received
        get_item_name: callable taking a NetworkItem and returning its name

        Stops on an unmapped item or a bridge error. Later items are not
        delivered out of order.
        """
        while self.next_index < len(items_received):
            index = self.next_index
            network_item = items_received[index]
            item_name = get_item_name(network_item)

            if item_name == "__Victory__":
                self._advance()
                continue

            mapping = ITEM_MAP.get(item_name)
            if mapping is None:
                log.error(
                    "No BotW actor mapping for AP item %r at index %d. "
                    "Delivery paused; add a mapping before continuing.",
                    item_name, index,
                )
                return False

            actor_name, quantity = mapping

            try:
                send_to_bridge(actor_name, quantity)
            except DeliveryError:
                log.exception(
                    "Failed to deliver AP item %r at index %d; "
                    "delivery paused.",
                    item_name, index,
                )
                return False

            # Advance only after receiving an OK from the bridge.
            self._advance()
            log.info(
                "Delivered AP item %d: %s -> %s x%d",
                index, item_name, actor_name, quantity,
            )

        return True

    def _advance(self):
        self.progress["next_index"] = self.next_index + 1
        _save_state(self.state)