
#!/usr/bin/env python3
"""Generate synchronized C++ and Python shrine-chest registries from CSV."""

import argparse
import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_REGISTRY = (
    REPO_ROOT / "check_inventory" / "shrine_chest_registry.csv"
)

DEFAULT_CPP_OUTPUT = (
    REPO_ROOT
    / "WiiXLaunch"
    / "mods"
    / "botw_ap_bridge"
    / "shrine_chest_registry.hpp"
)

DEFAULT_PYTHON_OUTPUT = (
    REPO_ROOT
    / "wiixlaunch-botw"
    / "tools"
    / "generated_shrine_chest_registry.py"
)

REQUIRED_COLUMNS = {
    "name",
    "persistent_flag_candidate",
}

VERIFIED_STATUSES = {
    "verified",
    "verified_match",
    "verified_assignment",
}


def parse_verified(value):
    return str(value or "").strip().lower() in {
        "1", "true", "yes", "verified"
    }


def cpp_string(value: str) -> str:
    """Escape a string as a C++ string literal."""
    return json.dumps(value, ensure_ascii=True)


def load_registry(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Registry CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)

        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "Registry CSV is missing required columns: "
                + ", ".join(sorted(missing))
            )

        entries = []
        seen_names = set()
        seen_flags = set()

        for line_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            flag = (row.get("persistent_flag_candidate") or "").strip()

            # Ignore completely empty CSV rows.
            if not name and not flag:
                continue

            if not name:
                raise ValueError(
                    f"CSV line {line_number}: location name is empty"
                )

            if not flag:
                raise ValueError(
                    f"CSV line {line_number}: persistent flag is empty "
                    f"for {name!r}"
                )

            if name in seen_names:
                raise ValueError(
                    f"Duplicate location name on CSV line "
                    f"{line_number}: {name!r}"
                )

            if flag in seen_flags:
                raise ValueError(
                    f"Duplicate persistent flag on CSV line "
                    f"{line_number}: {flag!r}"
                )

            seen_names.add(name)
            seen_flags.add(flag)

            raw_hash = (row.get("hash_id_unsigned") or "").strip()
            if raw_hash:
                try:
                    hash_id = int(raw_hash, 10)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid hash_id_unsigned on CSV line "
                        f"{line_number}: {raw_hash!r}"
                    ) from exc

                if not 0 <= hash_id <= 0xFFFFFFFF:
                    raise ValueError(
                        f"Hash ID out of uint32 range on CSV line "
                        f"{line_number}: {hash_id}"
                    )
            else:
                hash_id = 0

            status = (
                row.get("assignment_status") or "unknown"
            ).strip()

            entries.append(
                {
                    "name": name,
                    "persistent_flag": flag,
                    "drop_actor": (
                        row.get("drop_actor") or ""
                    ).strip(),
                    "hash_id_unsigned": hash_id,
                    "assignment_status": status,
                    "verified": parse_verified(row.get("verified", "")),
                }
            )

    if not entries:
        raise ValueError(f"No registry entries found in {path}")

    return entries


def generate_cpp(entries: list[dict]) -> str:
    lines = [
        "// Generated file. Do not edit by hand.",
        "// Source: check_inventory/shrine_chest_registry.csv",
        "#pragma once",
        "",
        "#include <cstddef>",
        "#include <cstdint>",
        "",
        "namespace BotWAP {",
        "",
        "struct ShrineChestEntry {",
        "    const char* location_name;",
        "    const char* persistent_flag;",
        "    const char* drop_actor;",
        "    std::uint32_t hash_id_unsigned;",
        "    const char* assignment_status;",
        "    bool verified;",
        "};",
        "",
        "inline constexpr ShrineChestEntry kShrineChestRegistry[] = {",
    ]

    for entry in entries:
        lines.append(
            "    {"
            f"{cpp_string(entry['name'])}, "
            f"{cpp_string(entry['persistent_flag'])}, "
            f"{cpp_string(entry['drop_actor'])}, "
            f"{entry['hash_id_unsigned']}u, "
            f"{cpp_string(entry['assignment_status'])}, "
            f"{'true' if entry['verified'] else 'false'}"
            "},"
        )

    lines.extend(
        [
            "};",
            "",
            "inline constexpr std::size_t kShrineChestRegistrySize =",
            "    sizeof(kShrineChestRegistry) / sizeof(kShrineChestRegistry[0]);",
            "",
            "}  // namespace BotWAP",
            "",
        ]
    )

    return "\n".join(lines)


def generate_python(entries: list[dict]) -> str:
    # JSON syntax is valid Python for these string, integer, and boolean values,
    # except JSON's true/false spellings. Emit Python literals explicitly.
    lines = [
        '"""Generated shrine chest registry. Do not edit by hand."""',
        "",
        "# Source: check_inventory/shrine_chest_registry.csv",
        "# current_sequential_id is intentionally not used as an AP runtime ID.",
        "",
        "SHRINE_CHEST_REGISTRY = (",
    ]

    for entry in entries:
        lines.extend(
            [
                "    {",
                f"        'name': {entry['name']!r},",
                f"        'persistent_flag': {entry['persistent_flag']!r},",
                f"        'drop_actor': {entry['drop_actor']!r},",
                f"        'hash_id_unsigned': {entry['hash_id_unsigned']},",
                f"        'assignment_status': "
                f"{entry['assignment_status']!r},",
                f"        'verified': "
                f"{'True' if entry['verified'] else 'False'},",
                "    },",
            ]
        )

    lines.extend(
        [
            ")",
            "",
            "SHRINE_CHEST_BY_NAME = {",
            "    entry['name']: entry for entry in SHRINE_CHEST_REGISTRY",
            "}",
            "",
        ]
    )

    return "\n".join(lines)


def write_if_changed(path: Path, content: str) -> bool:
    """Write output only when its contents have changed."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file() and path.read_text(encoding="utf-8") == content:
        print(f"Unchanged: {path}")
        return False

    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the BotW shrine chest registries."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Input shrine_chest_registry.csv",
    )
    parser.add_argument(
        "--cpp-out",
        type=Path,
        default=DEFAULT_CPP_OUTPUT,
        help="Output C++ header",
    )
    parser.add_argument(
        "--python-out",
        type=Path,
        default=DEFAULT_PYTHON_OUTPUT,
        help="Output Python module",
    )
    args = parser.parse_args()

    try:
        entries = load_registry(args.registry)
        write_if_changed(args.cpp_out, generate_cpp(entries))
        write_if_changed(args.python_out, generate_python(entries))

        verified_count = sum(entry["verified"] for entry in entries)

        print()
        print(f"Registry entries: {len(entries)}")
        print(f"Verified entries: {verified_count}")
        print(f"Provisional/unverified entries: {len(entries) - verified_count}")
        print("Note: verification status is copied from the CSV;")
        print("      generation does not validate game chest mappings.")

        return 0

    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())