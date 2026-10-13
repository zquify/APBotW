# APBotW

This workspace contains the Breath of the Wild Archipelago world and the
WiiXLaunch projects used to connect it to the game.

## Projects and data

- [`BotWArchipelago/`](./BotWArchipelago/) contains the Archipelago world
  implementation, its game data, hooks, and tests.
- [`WiiXLaunch/`](./WiiXLaunch/) contains the general-purpose C++ framework
  and SDK.
- [`wiixlaunch-botw/`](./wiixlaunch-botw/) contains the BotW-specific
  WiiXLaunch module.
- `WiiXLaunch/vendor/wiixlaunch-botw/` is the framework's vendored copy. It
  remains in place for framework builds; files with matching names in the
  top-level working copy are not necessarily identical.
- [`check_inventory/`](./check_inventory/) contains generated and reviewable
  CSV inventories used by the shrine-chest matching workflow.

## Tooling

Repository-wide and BotW integration scripts live under [`tools/`](./tools/):

- [`tools/archipelago/`](./tools/archipelago/) contains Archipelago client,
  inventory, and shrine-registry utilities.
- [`tools/wiixlaunch-botw/`](./tools/wiixlaunch-botw/) contains BotW asset
  packers, UI asset previewers, and the local build/deploy launcher.

The WiiXLaunch project's own build scripts, SDK utilities, and C++ test
programs remain under `WiiXLaunch/` because they are coupled to that project.
