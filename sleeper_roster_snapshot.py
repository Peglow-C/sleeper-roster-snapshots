#!/usr/bin/env python3
"""
sleeper_roster_snapshot.py

Pulls your current roster(s) from Sleeper and writes one JSON file per
league, named with the league name and today's date, so you can track
how your team looked at any point in the season.

Usage:
    python3 sleeper_roster_snapshot.py --username YOUR_SLEEPER_USERNAME

    # Only snapshot specific leagues (by league_id) instead of all of them:
    python3 sleeper_roster_snapshot.py --username YOUR_SLEEPER_USERNAME \
        --league-id 123456789012345678 --league-id 987654321098765432

    # Override season or output directory:
    python3 sleeper_roster_snapshot.py --username YOUR_SLEEPER_USERNAME \
        --season 2026 --outdir </path/to/roster/directory>

Requires: requests   (pip install requests)
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

API_BASE = "https://api.sleeper.app/v1"
# Paths are resolved from this file's location, so renaming or moving the
# project folder can't break the defaults.
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTDIR = str(BASE_DIR / "data" / "rosters")
PLAYERS_CACHE_PATH = BASE_DIR / "data" / "players_cache.json"


def get_json(url: str):
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_user_id(username: str) -> str:
    data = get_json(f"{API_BASE}/user/{username}")
    if not data or "user_id" not in data:
        sys.exit(f"Could not find a Sleeper user for username '{username}'")
    return data["user_id"]


def get_leagues(user_id: str, season: str):
    return get_json(f"{API_BASE}/user/{user_id}/leagues/nfl/{season}")


def get_rosters(league_id: str):
    return get_json(f"{API_BASE}/league/{league_id}/rosters")


def get_league_users(league_id: str):
    return get_json(f"{API_BASE}/league/{league_id}/users")


def load_players_cache(max_age_days: int = 1) -> dict:
    """
    The full /players/nfl payload is several MB and Sleeper asks that it
    not be pulled on every request, so we cache it locally and only
    refresh once a day.
    """
    if PLAYERS_CACHE_PATH.exists():
        age_days = (date.today() - date.fromtimestamp(PLAYERS_CACHE_PATH.stat().st_mtime)).days
        if age_days < max_age_days:
            with open(PLAYERS_CACHE_PATH, "r") as f:
                return json.load(f)

    print("Refreshing player ID -> name/position cache from Sleeper (this is a few MB)...")
    players = get_json(f"{API_BASE}/players/nfl")
    PLAYERS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAYERS_CACHE_PATH, "w") as f:
        json.dump(players, f)
    return players


def slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[\s_]+", "-", slug)


def build_roster_owner_map(league_users):
    """roster owners are matched to rosters via owner_id / user_id."""
    return {u["user_id"]: u.get("display_name") or u.get("username") for u in league_users}


def snapshot_league(league: dict, my_user_id: str, players: dict, outdir: Path):
    league_id = league["league_id"]
    league_name = league["name"]

    rosters = get_rosters(league_id)
    league_users = get_league_users(league_id)
    owner_map = build_roster_owner_map(league_users)

    my_roster = next((r for r in rosters if r.get("owner_id") == my_user_id), None)
    if my_roster is None:
        print(f"  Warning: couldn't find your roster in league '{league_name}', skipping.")
        return

    def player_info(pid: str):
        p = players.get(pid, {})
        return {
            "player_id": pid,
            "name": p.get("full_name") or pid,
            "position": p.get("position"),
            "team": p.get("team"),
            "status": p.get("injury_status"),
        }

    starter_ids = my_roster.get("starters", []) or []
    all_ids = my_roster.get("players", []) or []
    bench_ids = [pid for pid in all_ids if pid not in starter_ids]

    snapshot = {
        "captured_at": date.today().isoformat(),
        "league_id": league_id,
        "league_name": league_name,
        "season": league.get("season"),
        "week": league.get("settings", {}).get("leg"),
        "team_name": owner_map.get(my_user_id, "me"),
        "record": {
            "wins": my_roster.get("settings", {}).get("wins"),
            "losses": my_roster.get("settings", {}).get("losses"),
            "ties": my_roster.get("settings", {}).get("ties"),
            "points_for": my_roster.get("settings", {}).get("fpts"),
            "points_against": my_roster.get("settings", {}).get("fpts_against"),
        },
        "starters": [player_info(pid) for pid in starter_ids],
        "bench": [player_info(pid) for pid in bench_ids],
        "taxi": [player_info(pid) for pid in (my_roster.get("taxi") or [])],
        "ir": [player_info(pid) for pid in (my_roster.get("reserve") or [])],
    }

    outdir.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify(league_name)}_{date.today().isoformat()}.json"
    outpath = outdir / filename
    with open(outpath, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"  Wrote {outpath}")


def main():
    parser = argparse.ArgumentParser(description="Snapshot your Sleeper roster(s) to dated JSON files.")
    parser.add_argument("--username", required=True, help="Your Sleeper username")
    parser.add_argument("--season", default=str(date.today().year), help="NFL season year (default: current year)")
    parser.add_argument("--league-id", action="append", dest="league_ids",
                         help="Only snapshot this league_id. Repeatable. Defaults to all leagues for the season.")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Directory to write snapshot files into")
    args = parser.parse_args()

    outdir = Path(args.outdir)

    print(f"Looking up Sleeper user '{args.username}'...")
    user_id = get_user_id(args.username)

    print(f"Fetching leagues for season {args.season}...")
    leagues = get_leagues(user_id, args.season)
    if args.league_ids:
        leagues = [l for l in leagues if l["league_id"] in args.league_ids]

    if not leagues:
        sys.exit("No matching leagues found.")

    players = load_players_cache()

    for league in leagues:
        print(f"Snapshotting '{league['name']}'...")
        snapshot_league(league, user_id, players, outdir)

    print("Done.")


if __name__ == "__main__":
    main()