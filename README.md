# sleeper-roster-snapshots

Scripts that take snapshots of my Sleeper fantasy football rosters and compare them over the season.

## Contents

```
sleeper-roster-snapshots/
  sleeper_roster_snapshot.py   saves the current roster of each league as JSON
  sleeper_roster_diff.py       compares two snapshots of a league
  requirements.txt
  docs/                        Sleeper API documentation
  data/                        not in git (only on disk and in backups)
    rosters/                   snapshots, <league-slug>_<date>.json
    players_cache.json         Sleeper player list, refreshed once a day
    snapshot.log               output of the weekly cron job
    inbox/  archive/
```

## Setup

Needs `python3` with venv support (`sudo apt install python3-venv`).

```bash
cd <path/to/sleeper-roster-snapshots>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Recreate `.venv/` from `requirements.txt` after moving the folder, because virtualenvs can't be relocated.

## Usage

Activate the virtualenv first (`source .venv/bin/activate`).

### Snapshot

```bash
python3 sleeper_roster_snapshot.py --username <sleeper-username>
```

- Writes one file per league to `data/rosters/<league-slug>_<date>.json`. A second run on the same day overwrites that day's file.
- The first run downloads the player list (a few MB) to `data/players_cache.json`.

| Option | Meaning |
|---|---|
| `--username` | Sleeper username (required) |
| `--season` | NFL season year (default: current year) |
| `--league-id` | Only snapshot this league; repeat for several (default: all leagues) |
| `--outdir` | Output directory (default: `data/rosters`) |

### Scheduled snapshots (cron)

A cron job takes a snapshot at 19:00 (Central European time) on Sunday, Monday, Tuesday, Wednesday and Friday. 19:00 is the Sunday 1 PM ET kickoff. Add it with `crontab -e` as the user that owns the project folder, on the machine that runs the snapshots:

```cron
# 19:00 on Sun, Mon, Tue, Wed and Fri (0 = Sunday)
0 19 * * 0-3,5  cd <path/to/sleeper-roster-snapshots> && .venv/bin/python sleeper_roster_snapshot.py --username <sleeper-username> >> data/snapshot.log 2>&1
```

- Calling `.venv/bin/python` directly uses the virtualenv without activating it, so cron's minimal environment doesn't matter.
- Output from each run is appended to `data/snapshot.log`.
- Cron uses the machine's local time, so the machine must be on `Europe/Berlin` or a similar zone. Check it with `timedatectl` and set it with `sudo timedatectl set-timezone Europe/Berlin`.
- Europe leaves daylight saving time one week before the US does. In that week, 1 PM ET is 18:00, so the Sunday snapshot runs an hour after kickoff.
- If the machine is off at the scheduled time, that snapshot is skipped.

### Diff

```bash
# The two most recent snapshots of a league
python3 sleeper_roster_diff.py --dir data/rosters --league <league-slug>

# Two specific snapshots
python3 sleeper_roster_diff.py data/rosters/hardknocks_2026-09-16.json data/rosters/hardknocks_2026-10-06.json
```

- The league slug is the file name before the date, for example `hardknocks` or `twelve-bolievers`.
- Prints adds, drops, moves between starters, bench, taxi and IR, and record and points changes.
- `--out diff.json` also writes the diff as JSON.

## Reference

`docs/sleeper-api-documentation.md` describes the Sleeper endpoints the scripts use. The API is public and read-only, so no key is needed.
