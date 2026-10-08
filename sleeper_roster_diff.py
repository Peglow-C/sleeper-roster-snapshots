#!/usr/bin/env python3
"""
sleeper_roster_diff.py

Compares two roster snapshots produced by sleeper_roster_snapshot.py and
prints what changed: adds, drops, and moves between starters/bench/taxi/IR,
plus record and points changes.

Usage:
    # Compare two specific files:
    python3 sleeper_roster_diff.py old_snapshot.json new_snapshot.json

    # Or just point it at the snapshots directory + league name slug and
    # it will diff the two most recent snapshots for that league:
    python3 sleeper_roster_diff.py --dir <path/to/snapshot/directory> --league my-league-name

    # Also write the diff out as JSON instead of just printing it:
    python3 sleeper_roster_diff.py old.json new.json --out diff.json
"""

import argparse
import json
import sys
from pathlib import Path

SLOTS = ["starters", "bench", "taxi", "ir"]


def load_snapshot(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def index_players(snapshot: dict):
    """Map player_id -> (slot, player dict) across all roster spots."""
    index = {}
    for slot in SLOTS:
        for p in snapshot.get(slot, []):
            index[p["player_id"]] = (slot, p)
    return index


def find_latest_two(dir_path: Path, league_slug: str):
    files = sorted(dir_path.glob(f"{league_slug}_*.json"))
    if len(files) < 2:
        sys.exit(f"Need at least 2 snapshots matching '{league_slug}_*.json' in {dir_path}, found {len(files)}.")
    return files[-2], files[-1]


def diff_snapshots(old: dict, new: dict) -> dict:
    old_idx = index_players(old)
    new_idx = index_players(new)

    old_ids = set(old_idx)
    new_ids = set(new_idx)

    added = [new_idx[pid][1] | {"slot": new_idx[pid][0]} for pid in sorted(new_ids - old_ids)]
    dropped = [old_idx[pid][1] | {"slot": old_idx[pid][0]} for pid in sorted(old_ids - new_ids)]

    moved = []
    for pid in sorted(old_ids & new_ids):
        old_slot, old_p = old_idx[pid]
        new_slot, new_p = new_idx[pid]
        if old_slot != new_slot:
            moved.append({
                "player_id": pid,
                "name": new_p.get("name"),
                "from": old_slot,
                "to": new_slot,
            })

    old_rec = old.get("record", {})
    new_rec = new.get("record", {})
    record_change = {
        "wins": (old_rec.get("wins"), new_rec.get("wins")),
        "losses": (old_rec.get("losses"), new_rec.get("losses")),
        "ties": (old_rec.get("ties"), new_rec.get("ties")),
        "points_for": (old_rec.get("points_for"), new_rec.get("points_for")),
        "points_against": (old_rec.get("points_against"), new_rec.get("points_against")),
    }

    return {
        "league_name": new.get("league_name", old.get("league_name")),
        "from_date": old.get("captured_at"),
        "to_date": new.get("captured_at"),
        "added": added,
        "dropped": dropped,
        "moved": moved,
        "record_change": record_change,
    }


def print_diff(diff: dict):
    print(f"\n{diff['league_name']}: {diff['from_date']} -> {diff['to_date']}")
    print("=" * 60)

    if diff["added"]:
        print("\nAdded:")
        for p in diff["added"]:
            print(f"  + {p.get('name')} ({p.get('position')}, {p.get('team')}) -> {p['slot']}")
    else:
        print("\nAdded: none")

    if diff["dropped"]:
        print("\nDropped:")
        for p in diff["dropped"]:
            print(f"  - {p.get('name')} ({p.get('position')}, {p.get('team')}) was in {p['slot']}")
    else:
        print("\nDropped: none")

    if diff["moved"]:
        print("\nMoved:")
        for m in diff["moved"]:
            print(f"  ~ {m['name']}: {m['from']} -> {m['to']}")
    else:
        print("\nMoved: none")

    rc = diff["record_change"]
    print("\nRecord:")
    w = rc["wins"]; l = rc["losses"]; t = rc["ties"]
    print(f"  W-L-T: {w[0]}-{l[0]}-{t[0]}  ->  {w[1]}-{l[1]}-{t[1]}")
    pf = rc["points_for"]; pa = rc["points_against"]
    print(f"  Points for:     {pf[0]}  ->  {pf[1]}")
    print(f"  Points against: {pa[0]}  ->  {pa[1]}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Diff two Sleeper roster snapshots.")
    parser.add_argument("files", nargs="*", help="old_snapshot.json new_snapshot.json")
    parser.add_argument("--dir", help="Snapshots directory (use with --league to auto-pick the two most recent)")
    parser.add_argument("--league", help="League name slug to auto-pick the two most recent snapshots for")
    parser.add_argument("--out", help="Optional path to also write the diff as JSON")
    args = parser.parse_args()

    if args.dir and args.league:
        old_path, new_path = find_latest_two(Path(args.dir), args.league)
    elif len(args.files) == 2:
        old_path, new_path = Path(args.files[0]), Path(args.files[1])
    else:
        parser.error("Provide either two snapshot files, or --dir and --league to auto-select the latest two.")
        return

    old = load_snapshot(old_path)
    new = load_snapshot(new_path)

    diff = diff_snapshots(old, new)
    print_diff(diff)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(diff, f, indent=2)
        print(f"Diff written to {args.out}")


if __name__ == "__main__":
    main()