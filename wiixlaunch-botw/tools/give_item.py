
#!/usr/bin/env python3
"""Send an item-grant command to the WiiXLaunch BotW bridge."""

import argparse
import socket
import sys


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_TIMEOUT = 3.0


def send_item(host, port, actor, parameters, timeout):
    # Protocol: GIVE <actor> [parameter1 parameter2 ...]
    parts = ["GIVE", actor]
    parts.extend(str(value) for value in parameters)
    command = " ".join(parts) + "\n"

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(command.encode("ascii"))

        response = bytearray()
        while not response.endswith(b"\n"):
            chunk = sock.recv(1)
            if not chunk:
                break
            response.extend(chunk)

    if not response:
        raise RuntimeError("Bridge disconnected without responding.")

    return response.decode("ascii").strip()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Give a BotW item through WiiXLaunch. "
            "Parameters are passed to the bridge without clamping."
        )
    )
    parser.add_argument(
        "actor",
        help="BotW actor name, e.g. Item_Fruit_D",
    )
    parser.add_argument(
        "parameters",
        nargs="*",
        type=int,
        metavar="PARAM",
        help="Zero or more integer parameters; interpretation depends on the item",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)

    args = parser.parse_args()

    if not args.actor or any(c.isspace() for c in args.actor):
        parser.error("actor must be a name without whitespace")

    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    if args.timeout <= 0:
        parser.error("timeout must be greater than zero")

    try:
        response = send_item(
            args.host,
            args.port,
            args.actor,
            args.parameters,
            args.timeout,
        )
    except (OSError, RuntimeError, UnicodeError) as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        print(
            "Check that Cemu is running, BotW is loaded, and the bridge "
            "is listening on {}:{}.".format(args.host, args.port),
            file=sys.stderr,
        )
        return 1

    print("Bridge response: {}".format(response))

    if response == "OK":
        print(
            "Bridge accepted actor {!r} with parameters: {}".format(
                args.actor,
                args.parameters if args.parameters else "(none)",
            )
        )
        return 0

    print("The bridge did not confirm the command.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())