from BaseClasses import Entrance, ItemClassification, MultiWorld, Region
from .Helpers import is_location_enabled, is_event_enabled
from .Data import region_table
from .Locations import BotWLocation, location_name_to_location
from .Items import BotWItem
from worlds.AutoWorld import World


regionMap = dict(region_table)

# Use explicitly marked starting regions, or make every region
# reachable from Menu when none are explicitly marked.
starting_regions = [
    name for name, data in regionMap.items()
    if data.get("starting", False)
]

if not starting_regions:
    starting_regions = list(regionMap.keys())

default_region = starting_regions[0] if starting_regions else "Menu"


def create_regions(world: World, multiworld: MultiWorld, player: int):
    for region_name, region_data in regionMap.items():
        exits = region_data.get("connects_to", []) or []

        locations = [
            location["name"]
            for location in world.location_table
            if location.get("region", default_region) == region_name
            and is_location_enabled(multiworld, player, location)
        ]

        region = create_region(
            world,
            multiworld,
            player,
            region_name,
            locations,
            exits,
        )

        multiworld.regions.append(region)

    # Menu is now the native starting region.
    # There is no artificial "Manual" region anymore.
    menu = Region("Menu", player, multiworld)

    for region_name in starting_regions:
        menu.exits.append(
            Entrance(
                player,
                getConnectionName("Menu", region_name),
                menu,
            )
        )

    multiworld.regions.append(menu)

    # Connect normal region exits.
    for region_name, region_data in regionMap.items():
        for linked_region in region_data.get("connects_to", []) or []:
            connection = multiworld.get_entrance(
                getConnectionName(region_name, linked_region),
                player,
            )

            connection.connect(
                multiworld.get_region(linked_region, player)
            )

    # Connect Menu to starting regions.
    for region_name in starting_regions:
        connection = multiworld.get_entrance(
            getConnectionName("Menu", region_name),
            player,
        )

        connection.connect(
            multiworld.get_region(region_name, player)
        )


def create_region(
    world: World,
    multiworld: MultiWorld,
    player: int,
    name: str,
    locations=None,
    exits=None,
):
    region = Region(name, player, multiworld)

    for location_name in locations or []:
        location_id = world.location_name_to_id.get(location_name)

        location = BotWLocation(
            player,
            location_name,
            location_id,
            region,
        )

        location_data = location_name_to_location[location_name]

        if location_data.get("prehint"):
            world.options.start_location_hints.value.add(location_name)

        region.locations.append(location)

    for exit_name in exits or []:
        region.exits.append(
            Entrance(
                player,
                getConnectionName(name, exit_name),
                region,
            )
        )

    return region


def getConnectionName(entranceName: str, exitName: str):
    return entranceName + "To" + exitName


def create_events(world: World, multiworld: MultiWorld, player: int):
    for location_name, event in world.event_name_to_event.items():
        if not is_event_enabled(multiworld, player, event):
            continue

        region_name = event.get("region", default_region)

        region = multiworld.get_region(
            region_name,
            player,
        )

        item = BotWItem(
            event["name"],
            ItemClassification.progression,
            None,
            player=player,
        )

        location = BotWLocation(
            player,
            location_name,
            None,
            region,
        )

        region.locations.append(location)
        location.place_locked_item(item)