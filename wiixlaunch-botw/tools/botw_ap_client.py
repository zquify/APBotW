"""Native Breath of the Wild Archipelago item-delivery client."""

import argparse
import asyncio
import csv
import logging
import sys
import socket
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD_DIR = REPO_ROOT / "BotWArchipelago"

if not WORLD_DIR.is_dir():
    raise FileNotFoundError(
        f"Native BotW world directory not found: {WORLD_DIR}"
    )

# Archipelago installation containing CommonClient.py.
ARCHIPELAGO_DIR = Path(r"C:\Projects\Archipelago-0.6.7")

# Existing WiiXLaunch tools containing ap_delivery.py.
TOOLS_DIR = Path(r"C:\Projects\wiixlaunch-botw\tools")

sys.path.insert(0, str(ARCHIPELAGO_DIR))
sys.path.insert(0, str(TOOLS_DIR))

from CommonClient import CommonContext, get_base_parser, server_loop
from ap_delivery import APItemDelivery
from generated_shrine_chest_registry import SHRINE_CHEST_REGISTRY


GAME_NAME = "Breath of the Wild"

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


def resolve_location_id(ctx, location_name):
    """Resolve a location name using the native BotW world's IDs."""
    return NATIVE_LOCATION_IDS.get(location_name)


def load_native_location_ids():
    """Build the location-name mapping using the native world's ID rules."""
    import json

    game_file = WORLD_DIR / "data" / "game.json"
    data_file = WORLD_DIR / "data" / "locations.json"

    with game_file.open("r", encoding="utf-8-sig") as f:
        game_table = json.load(f)

    starting_index = int(game_table.get("starting_index", 1))

    with data_file.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    locations = data.get("data", data)
    count = starting_index
    name_to_id = {}

    for location in locations:
        if "id" in location:
            location_id = location["id"]
            if location_id >= count:
                count = location_id
            else:
                raise ValueError(
                    f"Invalid location ID for {location['name']}: "
                    f"{location_id}"
                )

        location_id = count
        name_to_id[location["name"]] = location_id
        count += 1

    return name_to_id


NATIVE_LOCATION_IDS = load_native_location_ids()


def load_shrine_locations():
    """Build Dungeon index -> (AP location ID, location name)."""
    mapping_file = (
        REPO_ROOT
        / "check_inventory"
        / "shrine_dungeon_mapping.csv"
    )

    shrine_locations = {}

    with mapping_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Each shrine appears twice in the CSV: once for Dungeon.xmsbt
            # and once for LocationMarker.xmsbt. Only need one copy.
            if row["source_file"] != "Dungeon.xmsbt":
                continue

            dungeon_id = row["dungeon_id"]

            if not dungeon_id.startswith("Dungeon"):
                continue

            dungeon_number = int(
                dungeon_id.removeprefix("Dungeon")
            )

            shrine_name = row["display_name"]
            location_id = NATIVE_LOCATION_IDS.get(shrine_name)

            if location_id is None:
                raise ValueError(
                    f"Shrine {shrine_name!r} from {dungeon_id} "
                    "does not exist in locations.json"
                )

            shrine_locations[dungeon_number] = (
                location_id,
                shrine_name,
            )

    return shrine_locations


SHRINE_LOCATIONS = load_shrine_locations()


async def game_check_loop(ctx):
    """Poll the bridge and report the Oman Au Shrine completion."""
    while not ctx.exit_event.is_set():
        try:
            # Wait until Archipelago has authenticated this client.
            if ctx.slot is not None and ctx.server is not None:
                response = await asyncio.to_thread(
                    bridge_command, "POLL"
                )

                if response.startswith("CHECK SHRINE "):
                    try:
                        shrine_number = int(
                            response.removeprefix("CHECK SHRINE ").strip()
                        )
                    except ValueError:
                        logger.warning(
                            "Invalid shrine-check response from bridge: %r",
                            response,
                        )
                        continue

                    shrine = SHRINE_LOCATIONS.get(shrine_number)

                    if shrine is None:
                        logger.warning(
                            "No AP location mapping for Dungeon%03d",
                            shrine_number,
                        )
                        continue

                    location_id, check_name = shrine
                    ack_command = f"ACK SHRINE {shrine_number}"

                elif response.startswith("CHECK CHEST "):
                    try:
                        registry_index = int(
                            response.removeprefix("CHECK CHEST ").strip()
                        )
                    except ValueError:
                        logger.warning(
                            "Invalid chest-check response from bridge: %r",
                            response,
                        )
                        continue

                    from generated_shrine_chest_registry import (
                        SHRINE_CHEST_REGISTRY,
                    )

                    if not (
                        0 <= registry_index < len(SHRINE_CHEST_REGISTRY)
                    ):
                        logger.warning(
                            "Chest registry index out of range: %s",
                            registry_index,
                        )
                        continue

                    entry = SHRINE_CHEST_REGISTRY[registry_index]
                    check_name = entry["name"]
                    location_id = resolve_location_id(ctx, check_name)
                    ack_command = f"ACK CHEST {registry_index}"

                    if location_id is None:
                        logger.warning(
                            "Cannot resolve AP location ID for %r; "
                            "leaving chest check pending",
                            check_name,
                        )
                        continue

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
