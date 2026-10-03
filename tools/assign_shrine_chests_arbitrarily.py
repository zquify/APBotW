
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Projects\APBotW")
OUT = ROOT / "check_inventory"

AP_INVENTORY = OUT / "ap_location_inventory.csv"
CHEST_INVENTORY = OUT / "chest_actor_inventory.csv"
DUNGEON_MAPPING = OUT / "shrine_dungeon_mapping.csv"

REGISTRY_OUT = OUT / "shrine_chest_registry.csv"
SUMMARY_OUT = OUT / "shrine_chest_assignment_summary.csv"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(value):
    value = (value or "").strip().lower()
    value = re.sub(r"\s*-\s*chest\s*\d*\s*$", "", value)
    value = re.sub(r"\s+shrine\s*$", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


def dungeon_number(value):
    match = re.search(r"Dungeon(\d+)", value or "", re.I)
    return match.group(1) if match else None


def first_value(row, *names):
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def main():
    ap_rows = read_csv(AP_INVENTORY)
    chest_rows = read_csv(CHEST_INVENTORY)
    mapping_rows = read_csv(DUNGEON_MAPPING)

        # Preserve verification decisions when regenerating the registry.
    existing_verified = {}

    if REGISTRY_OUT.is_file():
        for row in read_csv(REGISTRY_OUT):
            name = (row.get("name") or "").strip()
            if name:
                existing_verified[name] = (
                    row.get("verified") or ""
                ).strip()

    # Resolve each shrine name to a dungeon number using the existing
    # message-table mapping report.
    shrine_to_dungeon = defaultdict(set)

    for row in mapping_rows:
        values = list(row.values())
        dungeon_ids = {
            number
            for value in values
            if (number := dungeon_number(value)) is not None
        }

        # A mapping row must identify one dungeon and a shrine name.
        if len(dungeon_ids) != 1:
            continue

        dungeon = next(iter(dungeon_ids))

        for value in values:
            text = str(value or "").strip()
            if not text or "shrine" not in text.lower():
                continue

            key = norm(text)
            if key:
                shrine_to_dungeon[key].add(dungeon)

    # Collect AP shrine chest checks by shrine.
    ap_by_shrine = defaultdict(list)

    for row in ap_rows:
        check_type = first_value(row, "check_type").lower()
        name = first_value(row, "name", "location_name")

        if check_type != "shrine_chest":
            continue

        match = re.search(r"^(.*?)\s*-\s*Chest(?:\s+(\d+))?$", name, re.I)
        if not match:
            continue

        shrine_name = match.group(1).strip()
        chest_number = int(match.group(2) or 1)

        ap_by_shrine[norm(shrine_name)].append({
            "current_sequential_id": first_value(
                row, "current_sequential_id"
            ),
            "name": name,
            "shrine_name": shrine_name,
            "chest_number": chest_number,
            "region": first_value(row, "region"),
            "categories": first_value(row, "categories"),
        })
    # Index actors by dungeon. Prefer Static map records when the same
    # HashId appears in both Static and Dynamic files.
    actors_by_dungeon = defaultdict(dict)

    for row in chest_rows:
        actor_name = first_value(row, "actor_name")
        map_file = first_value(row, "map_file")
        dungeon = dungeon_number(map_file)

        if not dungeon or not actor_name.startswith("TBox"):
            continue

        raw_hash = first_value(row, "hash_id_unsigned", "hash_id")
        if not raw_hash:
            continue

        try:
            hash_id = int(raw_hash) & 0xFFFFFFFF
        except ValueError:
            continue

        map_kind = first_value(row, "map_kind").lower()
        is_static = "static" in map_file.lower() or map_kind == "static"

        actor = {
            "map_file": map_file,
            "actor_name": actor_name,
            "hash_id": hash_id,
            "drop_actor": first_value(row, "drop_actor"),
            "drop_table": first_value(row, "drop_table"),
            "persistent_flag": first_value(
                row, "persistent_flag_candidate"
            ),
            "review_status": first_value(row, "review_status"),
            "is_static": is_static,
        }

        previous = actors_by_dungeon[dungeon].get(hash_id)

        # Prefer the Static record when duplicate HashIds exist.
        if previous is None or (is_static and not previous["is_static"]):
            actors_by_dungeon[dungeon][hash_id] = actor

    registry = []
    summary = []

    for shrine_key, checks in sorted(ap_by_shrine.items()):
        checks.sort(key=lambda x: (x["chest_number"], x["name"].lower()))

        dungeon_candidates = shrine_to_dungeon.get(shrine_key, set())

        if len(dungeon_candidates) != 1:
            reason = (
                "missing_dungeon_mapping"
                if not dungeon_candidates
                else "ambiguous_dungeon_mapping"
            )
            summary.append({
                "shrine": checks[0]["shrine_name"],
                "dungeon": "",
                "ap_chest_checks": len(checks),
                "unique_chest_actors": 0,
                "assigned": 0,
                "status": reason,
            })

            for check in checks:
                registry.append({
                    **check,
                    "dungeon": "",
                    "map_file": "",
                    "actor_name": "",
                    "hash_id_unsigned": "",
                    "drop_actor": "",
                    "drop_table": "",
                    "persistent_flag_candidate": "",
                    "assignment_status": reason,
                })
            continue

        dungeon = next(iter(dungeon_candidates))
        actors = sorted(
            actors_by_dungeon.get(dungeon, {}).values(),
            key=lambda actor: actor["hash_id"],
        )

        assigned_count = min(len(checks), len(actors))

        if len(checks) == len(actors):
            status = "provisional_assignment"
        else:
            status = "count_mismatch"

        summary.append({
            "shrine": checks[0]["shrine_name"],
            "dungeon": f"Dungeon{dungeon}",
            "ap_chest_checks": len(checks),
            "unique_chest_actors": len(actors),
            "assigned": assigned_count,
            "status": status,
        })

        for index, check in enumerate(checks):
            actor = actors[index] if index < assigned_count else None

            registry.append({
                **check,
                "dungeon": f"Dungeon{dungeon}",
                "map_file": actor["map_file"] if actor else "",
                "actor_name": actor["actor_name"] if actor else "",
                "hash_id_unsigned": actor["hash_id"] if actor else "",
                "drop_actor": actor["drop_actor"] if actor else "",
                "drop_table": actor["drop_table"] if actor else "",
                "persistent_flag_candidate": (
                    actor["persistent_flag"] if actor else ""
                ),
                "assignment_status": (
                    "provisional_assignment"
                    if actor
                    else "unassigned_count_mismatch"
                ),
                "verified": existing_verified.get(check["name"], ""),
            })

    registry_fields = [
        "current_sequential_id",
        "name", "shrine_name", "chest_number", "region", "categories",
        "dungeon", "map_file", "actor_name", "hash_id_unsigned",
        "drop_actor", "drop_table", "persistent_flag_candidate",
        "assignment_status", "verified",
    ]
    summary_fields = [
        "shrine", "dungeon", "ap_chest_checks",
        "unique_chest_actors", "assigned", "status",
    ]

    for path, rows, fields in [
        (REGISTRY_OUT, registry, registry_fields),
        (SUMMARY_OUT, summary, summary_fields),
    ]:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    print(f"AP shrine chest checks: {len(registry)}")
    print(f"Provisional assignments: {sum(r['assignment_status'] == 'provisional_assignment' for r in registry)}")
    print(f"Unassigned or unresolved: {sum(r['assignment_status'] != 'provisional_assignment' for r in registry)}")
    print(f"Registry: {REGISTRY_OUT}")
    print(f"Summary:  {SUMMARY_OUT}")


if __name__ == "__main__":
    main()