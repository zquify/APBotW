"""Native Breath of the Wild Archipelago item-delivery client."""

import argparse
import asyncio
import logging
import sys
import socket
from pathlib import Path

# Reuse the existing WiiXLaunch delivery bridge.
TOOLS_DIR = Path(r"C:\Projects\wiixlaunch-botw\tools")
sys.path.insert(0, str(TOOLS_DIR))

from CommonClient import CommonContext, get_base_parser, server_loop
from ap_delivery import APItemDelivery


GAME_NAME = "Breath of the Wild"

# Locations.py assigns IDs sequentially, starting at 1 by default.
# Oman Au Shrine is the eighth entry in data/locations.json.
OMAN_AU_SHRINE_LOCATION_ID = 8
OMAN_AU_CHEST_LOCATION_ID = 7

BRIDGE_ADDRESS = ("127.0.0.1", 8080)


def bridge_command(command):
    """Send one newline-terminated command to the WiiXLaunch bridge."""
    with socket.create_connection(BRIDGE_ADDRESS, timeout=2) as sock:
        sock.settimeout(2)
        sock.sendall((command + "\n").encode("ascii"))

        response = bytearray()
        while not response.endswith(b"\n"):
            chunk = sock.recv(128)
            if not chunk:
                break
            response.extend(chunk)

        return response.decode("ascii", errors="replace").strip()


async def game_check_loop(ctx):
    """Poll the bridge and report the Oman Au Shrine completion."""
    while not ctx.exit_event.is_set():
        try:
            # Wait until Archipelago has authenticated this client.
            if ctx.slot is not None and ctx.server is not None:
                response = await asyncio.to_thread(
                    bridge_command, "POLL"
                )

                if response == "CHECK OMAN_AU":
                    location_id = OMAN_AU_SHRINE_LOCATION_ID
                    check_name = "Oman Au Shrine"
                    ack_command = "ACK OMAN_AU"

                elif response == "CHECK OMAN_AU_CHEST":
                    location_id = OMAN_AU_CHEST_LOCATION_ID
                    check_name = "Oman Au Shrine - Chest"
                    ack_command = "ACK OMAN_AU_CHEST"

                else:
                    location_id = None

                if location_id is not None:
                    if location_id in ctx.checked_locations:
                        # The server already knows this check.
                        bridge_command(ack_command)

                    elif location_id in ctx.missing_locations:
                        sent = await ctx.check_locations({location_id})

                        if location_id in sent:
                            logger.info(
                                "Submitted location check: %s",
                                check_name,
                            )
                            bridge_command(ack_command)

        except (OSError, asyncio.TimeoutError):
            # Cemu or the bridge may not be ready yet.
            logger.debug("BotW bridge is not reachable yet.")

        except Exception:
            logger.exception("Error processing a BotW location check.")

        await asyncio.sleep(0.5)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BotWAP.Client")


class BotWContext(CommonContext):
    game = None
    items_handling = 0b111
    tags = {"AP"}
    want_slot_data = True

    def __init__(self, server_address=None, password=None):
        # Initialize CommonContext without assuming the custom game's
        # data package is already installed in this Python environment.
        super().__init__(server_address, password)

        # Set the native game after CommonContext initialization.
        self.game = GAME_NAME
        self.delivery = None

    async def server_auth(self, password_requested=False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)

        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd, args):
        if cmd == "Connected":
            server = self.server_address or "unknown-server"
            slot_name = self.username or self.auth or "unknown-slot"

            self.delivery = APItemDelivery(
                "{}|{}".format(server, slot_name)
            )

            logger.info(
                "Connected to Archipelago as %s. "
                "Received items will be sent to WiiXLaunch.",
                slot_name,
            )

        elif cmd == "ReceivedItems":
            if self.delivery is None:
                logger.warning(
                    "Received items before connection setup; "
                    "waiting for the next item update."
                )
                return

            try:
                completed = self.delivery.process(
                    self.items_received,
                    lambda network_item: self.item_names.lookup_in_game(
                        network_item.item,
                        GAME_NAME,
                    ),
                )

                if not completed:
                    logger.warning(
                        "Delivery paused. Check the preceding log "
                        "for an unmapped item or bridge error."
                    )

            except Exception:
                logger.exception("Item delivery failed.")


async def main(args):
    ctx = BotWContext(args.connect, args.password)
    if args.name:
        ctx.auth = args.name

    ctx.server_task = asyncio.create_task(
        server_loop(ctx),
        name="BotW Archipelago server loop",
    )

    check_task = asyncio.create_task(
        game_check_loop(ctx),
        name="BotW shrine-check bridge",
    )

    ctx.run_cli()

    try:
        await ctx.exit_event.wait()
    finally:
        check_task.cancel()
        await ctx.shutdown()


def launch():
    parser = get_base_parser(
        description="Breath of the Wild Archipelago client."
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Archipelago slot name.",
    )
    args = parser.parse_args()
    asyncio.run(main(args))


if __name__ == "__main__":
    launch()
