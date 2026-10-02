
#!/usr/bin/env python3
"""Build BotW shrine-to-dungeon mappings and match AP shrine chests."""

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from html import unescape


KNOWN_VERIFIED = {
    "oman au shrine - chest": {
        "actor": "TBox_Dungeon_Iron",
        "hash_unsigned": "3375369818",
        "flag": "CDungeon_TBox_Dungeon_Iron_3375369818",
    }
}


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalize(text):
    """Normalize shrine names and AP location suffixes."""
    text = unescape(str(text or "")).strip().casefold()
    text = re.sub(r"\s*-\s*chest(?:\s+\d+)?\s*$", "", text)
    text = re.sub(r"\s+shrine\s*$", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def extract_entries(path):
    """
    Parse readable extracted XMSBT entries such as:
      <entry label="Dungeon072">
        <text>Dah Kaso Shrine</text>
      </entry>

    Also accepts DungeonNNN_master labels, but reduces them to
    the base DungeonNNN ID.
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    entries = []

    pattern = re.compile(
        r'<entry\b[^>]*\blabel\s*=\s*["\']([^"\']+)["\'][^>]*>'
        r'(.*?)</entry>',
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(text):
        label = unescape(match.group(1)).strip()
        body = match.group(2)

        text_match = re.search(
            r"<text\b[^>]*>(.*?)</text>",
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if not text_match:
            continue

        message = unescape(text_match.group(1))
        message = re.sub(r"<[^>]+>", "", message).strip()
        message = re.sub(r"\s+", " ", message)

        dungeon_match = re.match(r"^(Dungeon\d{3})(?:_|$)", label)
        if dungeon_match and message:
            entries.append({
                "dungeon_id": dungeon_match.group(1),
                "label": label,
                "message": message,
                "source_file": path.name,
            })

    return entries


def build_shrine_mapping(message_dir):
    sources = [
        message_dir / "Dungeon.xmsbt",
        message_dir / "LocationMarker.xmsbt",
    ]

    missing = [path for path in sources if not path.is_file()]
    if missing:
        raise SystemExit(
            "Missing message-table file(s):\n"
            + "\n".join(str(path) for path in missing)
        )

    # key -> distinct (dungeon ID, displayed shrine name, source)
    found = defaultdict(set)

    for source in sources:
        for entry in extract_entries(source):
            name = entry["message"]

            # Keep shrine-name entries only. Some Dungeon entries describe
            # floors, apparatus, or other text unrelated to shrine names.
            if "shrine" not in name.casefold():
                continue

            key = normalize(name)
            if not key:
                continue

            found[key].add((
                entry["dungeon_id"],
                name,
                entry["source_file"],
                entry["label"],
            ))

    mapping = {}
    mapping_rows = []

    for key, records in sorted(found.items()):
        dungeon_ids = sorted({record[0] for record in records})

        if len(dungeon_ids) == 1:
            status = "mapped"
            dungeon_id = dungeon_ids[0]
        else:
            status = "conflict"
            dungeon_id = ""

        mapping[key] = {
            "dungeon_id": dungeon_id,
            "status": status,
            "records": sorted(records),
        }

        for record in sorted(records):
            mapping_rows.append({
                "normalized_shrine_name": key,
                "display_name": record[1],
                "dungeon_id": record[0],
                "source_file": record[2],
                "message_label": record[3],
                "mapping_status": status,
            })

    return mapping, mapping_rows


def get_shrine_name(location_name):
    match = re.match(
        r"^(.*?)\s+Shrine\b",
        location_name.strip(),
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project",
        type=Path,
        default=Path(r"C:\Projects\APBotW"),
    )
    parser.add_argument(
        "--botw-tools",
        type=Path,
        default=Path(r"C:\Projects\botw-tools"),
    )
    args = parser.parse_args()

    inventory_dir = args.project / "check_inventory"
    ap_path = inventory_dir / "ap_location_inventory.csv"
    actors_path = inventory_dir / "chest_actor_inventory.csv"
    message_dir = args.botw_tools / "text" / "StaticMsg"

    for path in (ap_path, actors_path):
        if not path.is_file():
            raise SystemExit(f"Missing input CSV: {path}")

    ap_rows = read_csv(ap_path)
    actors = read_csv(actors_path)

    mapping, mapping_rows = build_shrine_mapping(message_dir)

    mapping_path = inventory_dir / "shrine_dungeon_mapping.csv"
    write_csv(
        mapping_path,
        mapping_rows,
        [
            "normalized_shrine_name",
            "display_name",
            "dungeon_id",
            "source_file",
            "message_label",
            "mapping_status",
        ],
    )

    shrine_chests = [
        row for row in ap_rows
        if row.get("check_type", "").strip() == "shrine_chest"
    ]

    report = []
    unmatched = []

    for ap in shrine_chests:
        location_name = ap.get("name", "").strip()
        shrine_name = get_shrine_name(location_name)
        key = normalize(shrine_name)
        entry = mapping.get(key)

        base = {
            "ap_location_name": location_name,
            "diagnostic_sequential_id": ap.get(
                "current_sequential_id", ""
            ),
            "region": ap.get("region", ""),
            "shrine_name": shrine_name,
            "dungeon_map": "",
        }

        if not entry:
            unmatched.append({
                **base,
                "status": "no_message_table_mapping",
                "notes": "No shrine-name entry found in either message table.",
            })
            continue

        if entry["status"] != "mapped":
            unmatched.append({
                **base,
                "status": "conflicting_message_table_mapping",
                "notes": "Multiple dungeon IDs found for this shrine name.",
            })
            continue

        dungeon_id = entry["dungeon_id"]
        base["dungeon_map"] = dungeon_id

        # The dungeon ID must occur in the map filename.
        map_actors = [
            actor for actor in actors
            if dungeon_id.casefold() in Path(
                actor.get("map_file", "")
            ).name.casefold()
        ]

        chest_actors = [
            actor for actor in map_actors
            if "tbox" in actor.get("actor_name", "").casefold()
        ]

        if not chest_actors:
            unmatched.append({
                **base,
                "status": "mapped_but_no_chest_actors",
                "notes": "Dungeon mapping exists, but no TBox actors matched.",
            })
            continue

        for actor in chest_actors:
            actor_name = actor.get("actor_name", "")
            unsigned_hash = actor.get("hash_id_unsigned", "")
            flag = actor.get("persistent_flag_candidate", "")

            verified_info = KNOWN_VERIFIED.get(location_name.casefold(), {})
            verified = (
                actor_name == verified_info.get("actor")
                and unsigned_hash == verified_info.get("hash_unsigned")
                and flag == verified_info.get("flag")
            )

            report.append({
                **base,
                "map_file": actor.get("map_file", ""),
                "actor_name": actor_name,
                "hash_id": actor.get("hash_id", ""),
                "hash_id_unsigned": unsigned_hash,
                "position": actor.get("position", ""),
                "drop_actor": actor.get("drop_actor", ""),
                "persistent_flag_candidate": flag,
                "status": "verified" if verified else "candidate",
                "notes": (
                    "End-to-end verified in Cemu."
                    if verified else
                    "Dungeon-level candidate only. Verify that this actor "
                    "corresponds to this particular AP chest location."
                ),
            })

    report_fields = [
        "ap_location_name",
        "diagnostic_sequential_id",
        "region",
        "shrine_name",
        "dungeon_map",
        "map_file",
        "actor_name",
        "hash_id",
        "hash_id_unsigned",
        "position",
        "drop_actor",
        "persistent_flag_candidate",
        "status",
        "notes",
    ]

    unmatched_fields = [
        "ap_location_name",
        "diagnostic_sequential_id",
        "region",
        "shrine_name",
        "dungeon_map",
        "status",
        "notes",
    ]

    report_path = inventory_dir / "shrine_chest_matching_report.csv"
    unmatched_path = inventory_dir / "shrine_chest_unmatched.csv"

    write_csv(report_path, report, report_fields)
    write_csv(unmatched_path, unmatched, unmatched_fields)

    mapping_statuses = Counter(
        row["mapping_status"] for row in mapping_rows
    )
    report_statuses = Counter(row["status"] for row in report)
    unmatched_statuses = Counter(row["status"] for row in unmatched)

    mapped_locations = sum(
        1 for row in shrine_chests
        if (
            (entry := mapping.get(
                normalize(get_shrine_name(row.get("name", "")))
            ))
            and entry["status"] == "mapped"
        )
    )

    print(f"AP shrine-chest locations: {len(shrine_chests)}")
    print(f"Distinct shrine names in AP chest checks: "
          f"{len({normalize(get_shrine_name(r.get('name', ''))) for r in shrine_chests})}")
    print(f"Shrine names extracted from message tables: {len(mapping)}")
    print(f"Unique shrine-name mappings: {mapping_statuses['mapped']}")
    print(f"Conflicting shrine-name mappings: {mapping_statuses['conflict']}")
    print(f"AP chest locations with a dungeon mapping: {mapped_locations}")
    print(f"AP chest locations without a usable mapping: "
          f"{len(shrine_chests) - mapped_locations}")
    print(f"Actor candidate rows: {len(report)}")
    print(f"Verified actor matches: {report_statuses['verified']}")
    print(f"Candidate actor rows: {report_statuses['candidate']}")
    print(f"Unmatched report rows: {len(unmatched)}")
    print(f"Unmatched reasons: {dict(unmatched_statuses)}")
    print("\nGenerated:")
    print(mapping_path)
    print(report_path)
    print(unmatched_path)


if __name__ == "__main__":
    main()