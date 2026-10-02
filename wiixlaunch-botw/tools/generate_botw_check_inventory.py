#!/usr/bin/env python3
"""Inventory APBotW locations, BotW chest actors, and shrine/dungeon flag candidates.

This generates reviewable CSV reports. It does not claim a candidate flag is
correct until validated against the game/save data.
"""
import argparse
import csv
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


CHEST_RE = re.compile(r"^TBox_", re.I)
DUNGEON_RE = re.compile(r"(?:Clear_)?Dungeon\d{3}", re.I)
TOPIC_RE = re.compile(r"shrine|dungeon|terminal|divine.?beast", re.I)


def tag(node):
    return node.tag.rsplit("}", 1)[-1]


def text_at(node, name):
    for child in node.iter():
        if tag(child) == name and child.text and child.text.strip():
            return child.text.strip()
    return ""


def actor_values(root):
    yield from root.findall("./*/value")
    yield from root.findall("./Rails/*/RailPoints/value")


def position(actor):
    for node in actor.iter():
        if tag(node) == "Translate":
            values = [
                (x.text or "").strip().rstrip("f")
                for x in node.iter()
                if tag(x) == "value" and x.text and x.text.strip()
            ]
            return ",".join(values)
    return ""


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def check_type(name):
    n = name.lower()
    if "shrine" in n and "chest" in n:
        return "shrine_chest"
    if "shrine" in n:
        return "shrine_completion"
    if "terminal" in n or "divine beast" in n or "vah " in n:
        return "divine_beast_or_terminal"
    if "chest" in n:
        return "other_chest"
    return "other"


def read_locations(path):
    import json
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = obj.get("data", []) if isinstance(obj, dict) else obj
    return [r for r in rows if isinstance(r, dict) and r.get("name")]


def scan_chests(tools_root):
    rows = []
    for folder_name, kind in (
        ("mubin_dungeon", "dungeon"),
        ("mubin_trial", "trial"),
        ("mubin", "overworld"),
    ):
        folder = tools_root / folder_name
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.xml")):
            try:
                root = ET.parse(path).getroot()
            except (ET.ParseError, OSError) as exc:
                rows.append({"map_kind": kind, "map_file": path.name,
                             "review_status": "xml_parse_error: " + str(exc)})
                continue
            for actor in actor_values(root):
                actor_name = text_at(actor, "UnitConfigName")
                if not CHEST_RE.match(actor_name):
                    continue
                raw_hash = actor.attrib.get("HashId", "")
                try:
                    unsigned_hash = str(int(raw_hash) & 0xFFFFFFFF) if raw_hash else ""
                except ValueError:
                    unsigned_hash = ""
                params = next((n for n in actor.iter() if tag(n) == "_Parameters"), None)
                rows.append({
                    "map_kind": kind,
                    "map_file": path.name,
                    "actor_name": actor_name,
                    "hash_id": raw_hash,
                    "hash_id_unsigned": unsigned_hash,
                    "position": position(actor),
                    "drop_actor": ";".join(
                        (n.text or "").strip() for n in actor.iter()
                        if tag(n) == "DropActor" and n.text
                    ),
                    "drop_table": ";".join(
                        (n.text or "").strip() for n in actor.iter()
                        if tag(n) == "DropTable" and n.text
                    ),
                    "enable_revival": text_at(params, "EnableRevival") if params is not None else "",
                    "is_in_ground": text_at(params, "IsInGround") if params is not None else "",
                    # This pattern is confirmed for Oman Au only; other rows are candidates.
                    "persistent_flag_candidate": (
                        f"CDungeon_{actor_name}_{unsigned_hash}"
                        if kind in ("dungeon", "trial") and unsigned_hash else ""
                    ),
                    "review_status": "candidate_needs_flag_validation",
                })
    return rows


def scan_flag_candidates(tools_root):
    root = tools_root / "gamedata"
    rows, seen = [], set()
    if not root.is_dir():
        return rows
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(content.splitlines(), 1):
            if not TOPIC_RE.search(line) and not DUNGEON_RE.search(line):
                continue
            identifiers = sorted(set(DUNGEON_RE.findall(line)), key=str.lower)
            snippet = re.sub(r"\s+", " ", line.strip())[:500]
            key = (str(path.relative_to(tools_root)), line_no, snippet)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "source_file": key[0],
                "line": line_no,
                "dungeon_identifiers": ";".join(identifiers),
                "snippet": snippet,
                "review_status": "candidate_needs_semantic_validation",
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ap-repo", required=True, type=Path,
                        help="APBotW repository root (contains BotWArchipelago/).")
    parser.add_argument("--botw-tools", required=True, type=Path,
                        help="Local MrCheeze/botw-tools checkout.")
    parser.add_argument("--out", type=Path, default=Path("botw_check_inventory"),
                        help="Output folder.")
    args = parser.parse_args()

    locations_file = args.ap_repo / "BotWArchipelago" / "data" / "locations.json"
    if not locations_file.is_file():
        parser.error(f"AP locations file not found: {locations_file}")
    if not args.botw_tools.is_dir():
        parser.error(f"botw-tools folder not found: {args.botw_tools}")

    locations = read_locations(locations_file)
    loc_rows = []
    for i, loc in enumerate(locations, 1):
        categories = loc.get("category", [])
        loc_rows.append({
            "current_sequential_id": i,
            "name": loc["name"],
            "region": loc.get("region", ""),
            "categories": ";".join(categories) if isinstance(categories, list) else str(categories),
            "check_type": check_type(loc["name"]),
            "match_status": "not_mapped_yet",
        })

    chest_rows = scan_chests(args.botw_tools)
    flag_rows = scan_flag_candidates(args.botw_tools)
    args.out.mkdir(parents=True, exist_ok=True)

    write_csv(args.out / "ap_location_inventory.csv", loc_rows,
              ["current_sequential_id", "name", "region", "categories", "check_type", "match_status"])
    write_csv(args.out / "chest_actor_inventory.csv", chest_rows,
              ["map_kind", "map_file", "actor_name", "hash_id", "hash_id_unsigned", "position",
               "drop_actor", "drop_table", "enable_revival", "is_in_ground",
               "persistent_flag_candidate", "review_status"])
    write_csv(args.out / "shrine_completion_candidates.csv", flag_rows,
              ["source_file", "line", "dungeon_identifiers", "snippet", "review_status"])

    counts = Counter(r["check_type"] for r in loc_rows)
    map_counts = Counter(r["map_kind"] for r in chest_rows)
    print(f"AP locations inventoried: {len(loc_rows)}")
    for kind, count in sorted(counts.items()):
        print(f"  {kind}: {count}")
    print(f"Chest actors found: {len(chest_rows)}")
    for kind, count in sorted(map_counts.items()):
        print(f"  {kind}: {count}")
    print(f"Shrine/dungeon text candidates: {len(flag_rows)}")
    print(f"CSV reports: {args.out.resolve()}")
    print("Candidate flags are not confirmed mappings; validate before using them at runtime.")


if __name__ == "__main__":
    main()
