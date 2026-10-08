# Sleeper API Documentation

## Introduction

The Sleeper API is a read-only HTTP API that is free to use for **non-commercial purposes** and allows access to a user's leagues, drafts, and rosters.

For commercial use of the Sleeper API, please reach out to Sleeper directly to discuss licensing.

No API token is necessary, as you **cannot modify** contents via this API.

> **Rate limiting:** Be mindful of the frequency of calls. A general rule is to stay under 1000 API calls per minute, otherwise you risk being IP-blocked.

---

## User

### Fetch a user

```
GET https://api.sleeper.app/v1/user/<username>
GET https://api.sleeper.app/v1/user/<user_id>
```

```shell
curl "https://api.sleeper.app/v1/user/<username>"
curl "https://api.sleeper.app/v1/user/<user_id>"
```

Example response:

```json
{
  "username": "sleeperuser",
  "user_id": "12345678",
  "display_name": "SleeperUser",
  "avatar": "cc12ec49965eb7856f84d71cf85306af"
}
```

No authentication is performed since the API is read-only and only contains league information. You can GET the user object by providing either the `username` or the `user_id`.

> **Note:** The `username` of a user can change over time, so if you are storing information, hold onto the `user_id` instead.

---

## Avatars

Users and leagues have **avatar** images. There are thumbnail and full-size versions of each avatar.

| Type | URL |
|---|---|
| Full size | `https://sleepercdn.com/avatars/<avatar_id>` |
| Thumbnail | `https://sleepercdn.com/avatars/thumbs/<avatar_id>` |

---

## Leagues

### Get all leagues for a user

```
GET https://api.sleeper.app/v1/user/<user_id>/leagues/<sport>/<season>
```

```shell
curl "https://api.sleeper.app/v1/user/<user_id>/leagues/nfl/2018"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `user_id` | The numerical ID of the user. |
| `sport` | Only `nfl` is currently supported. |
| `season` | Season, e.g. `2017`, `2018`, etc. |

Example response:

```javascript
[
  {
    "total_rosters": 12,
    "status": "pre_draft", // can also be "drafting", "in_season", or "complete"
    "sport": "nfl",
    "settings": { settings object },
    "season_type": "regular",
    "season": "2018",
    "scoring_settings": { scoring_settings object },
    "roster_positions": [ roster positions array ],
    "previous_league_id": "198946952535085056",
    "name": "Sleeperbot Friends League",
    "league_id": "289646328504385536",
    "draft_id": "289646328508579840",
    "avatar": "efaefa889ae24046a53265a3c71b8b64"
  },
  ...
]
```

### Get a specific league

```
GET https://api.sleeper.app/v1/league/<league_id>
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve. |

Example response:

```javascript
{
  "total_rosters": 12,
  "status": "in_season",
  "sport": "nfl",
  "settings": { settings object },
  "season_type": "regular",
  "season": "2018",
  "scoring_settings": { scoring_settings object },
  "roster_positions": [ roster positions array ],
  "previous_league_id": "198946952535085056",
  "name": "Sleeperbot Dynasty",
  "league_id": "289646328504385536",
  "draft_id": "289646328508579840",
  "avatar": "efaefa889ae24046a53265a3c71b8b64"
}
```

### Getting rosters in a league

```
GET https://api.sleeper.app/v1/league/<league_id>/rosters
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/rosters"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve rosters from. |

Example response:

```javascript
[
  {
    "starters": ["2307", "2257", "4034", "147", "642", "4039", "515", "4149", "DET"],
    "settings": {
      "wins": 5,
      "waiver_position": 7,
      "waiver_budget_used": 0,
      "total_moves": 0,
      "ties": 0,
      "losses": 9,
      "fpts_decimal": 78,
      "fpts_against_decimal": 32,
      "fpts_against": 1670,
      "fpts": 1617
    },
    "roster_id": 1,
    "reserve": [],
    "players": ["1046", "138", "147", "2257", "2307", "2319", "4034", "4039", "4040", "4149", "421", "515", "642", "745", "DET"],
    "owner_id": "188815879448829952",
    "league_id": "206827432160788480"
  },
  ...
]
```

### Getting users in a league

```
GET https://api.sleeper.app/v1/league/<league_id>/users
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/users"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve users from. |

This endpoint also returns each user's **display_name**, **avatar**, and **metadata**, which sometimes includes a nickname they've given their team.

Example response:

```javascript
[
  {
    "user_id": "<user_id>",
    "username": "<username>",
    "display_name": "<display_name>",
    "avatar": "1233456789",
    "metadata": {
      "team_name": "Dezpacito"
    },
    "is_owner": true   // is commissioner (there can be multiple commissioners)
  },
  ...
]
```

### Getting matchups in a league

```
GET https://api.sleeper.app/v1/league/<league_id>/matchups/<week>
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/matchups/<week>"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve matchups from. |
| `week` | The week these matchups take place. |

Each object in the response list represents one team. The two teams sharing the same `matchup_id` are matched up against each other. `starters` is an ordered list of player IDs, and `players` is a list of all player IDs in the matchup — the bench can be deduced by removing `starters` from `players`.

Example response:

```javascript
[
  {
    "starters": ["421", "4035", "3242", "2133", "2449", "4531", "2257", "788", "PHI"],
    "roster_id": 1,
    "players": ["1352", "1387", "2118", "2133", "2182", "223", "2319", "2449", "3208", "4035", "421", "4881", "4892", "788", "CLE"],
    "matchup_id": 2,
    "points": 20.0,      // total points for team based on league settings
    "custom_points": null // if commissioner overrides points manually
  },
  ...
]
```

### Getting the playoff bracket

```
GET https://api.sleeper.app/v1/league/<league_id>/winners_bracket
GET https://api.sleeper.app/v1/league/<league_id>/loses_bracket
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/winners_bracket"
curl "https://api.sleeper.app/v1/league/<league_id>/losers_bracket"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve matchups from. |

Retrieves the playoff bracket for a league (supports 4, 6, and 8 team playoffs). Each row represents a matchup between two teams.

| Field | Type | Description |
|---|---|---|
| `r` | int | The round for this matchup — 1st, 2nd, 3rd, etc. |
| `m` | int | The match `id` of the matchup, unique within the bracket. |
| `t1` | int | The `roster_id` of a team in this matchup, or `{w: 1}` meaning "winner of match id 1". |
| `t2` | int | The `roster_id` of the other team, or `{l: 1}` meaning "loser of match id 1". |
| `w` | int | The `roster_id` of the winning team, once the match has been played. |
| `l` | int | The `roster_id` of the losing team, once the match has been played. |
| `t1_from` | object | Where `t1` comes from — the winner or loser of a given match `id` — needed to show bracket progression. |
| `t2_from` | object | Where `t2` comes from — the winner or loser of a given match `id` — needed to show bracket progression. |

Example response:

```javascript
[
  {r: 1, m: 1,   t1: 3,    t2: 6,     w: null, l: null},
  {r: 1, m: 2,   t1: 4,    t2: 5,     w: null, l: null},

  {r: 2, m: 3,   t1: 1,    t2: null,  t2_from: {w: 1},  w: null, l: null},
  {r: 2, m: 4,   t1: 2,    t2: null,  t2_from: {w: 2},  w: null, l: null},
  {r: 2, m: 5,   t1: null, t2: null,  t1_from: {l: 1},  t2_from: {l: 2},  w: null, l: null, p: 5},

  {r: 3, m: 6,   t1: null, t2: null,  t1_from: {w: 3},  t2_from: {w: 4},  w: null, l: null, p: 1},
  {r: 3, m: 7,   t1: null, t2: null,  t1_from: {l: 3},  t2_from: {l: 4},  w: null, l: null, p: 3}
]
```

### Get transactions

```
GET https://api.sleeper.app/v1/league/<league_id>/transactions/<round>
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/transactions/<round>"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve transactions for. |
| `round` | The week you want to pull from. |

Retrieves all free agent transactions, waivers, and trades.

Example response (trade):

```javascript
[
  {
    "type": "trade",
    "transaction_id": "434852362033561600",
    "status_updated": 1558039402803,
    "status": "complete",
    "settings": null,     // trades do not use this field
    "roster_ids": [2, 1], // roster_ids involved in this transaction
    "metadata": null,
    "leg": 1,              // in football, this is the week
    "drops": null,
    "draft_picks": [       // picks that were traded
      {
        "season": "2019",         // the season this draft pick belongs to
        "round": 5,                // which round this draft pick is
        "roster_id": 1,            // original owner's roster_id
        "previous_owner_id": 1,    // previous owner's roster id (in this trade)
        "owner_id": 2              // the new owner of this pick after the trade
      },
      {
        "season": "2019",
        "round": 3,
        "roster_id": 2,
        "previous_owner_id": 2,
        "owner_id": 1
      }
    ],
    "creator": "160000000000000000", // user id who initiated the transaction
    "created": 1558039391576,
    "consenter_ids": [2, 1],        // roster_ids of the people who agreed to this transaction
    "adds": null,
    "waiver_budget": [               // roster_id 2 sends 55 FAAB dollars to roster_id 3
      {
        "sender": 2,
        "receiver": 3,
        "amount": 55
      }
    ]
  },
  {
    "type": "free_agent", // could be waiver or trade as well
    "transaction_id": "434890120798142464",
    "status_updated": 1558048393967,
    "status": "complete",
    "settings": null,      // could be {'waiver_bid': 44} if it's FAAB waivers
    "roster_ids": [1],     // roster_ids involved in this transaction
    "metadata": null,      // can contain notes in waivers like why it didn't go through
    "leg": 1,
    "drops": {
      "1736": 1            // player id 1736 dropped from roster_id 1
    },
    "draft_picks": [],
    "creator": "160000000000000000",
    "created": 1558048393967,
    "consenter_ids": [1],  // the roster_ids who agreed to this transaction
    "adds": {
      "2315": 1             // player id 2315 added to roster_id 1
      ...
    },
    "waiver_budget": []     // this is used for trades only involving FAAB
  },
  ...
]
```

### Get traded picks

```
GET https://api.sleeper.app/v1/league/<league_id>/traded_picks
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/traded_picks"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve traded picks for. |

Retrieves all traded picks in a league, including future picks.

Example response:

```javascript
[
  {
    "season": "2019",        // which season the pick is for
    "round": 5,               // which round the pick is
    "roster_id": 1,           // roster_id of ORIGINAL owner
    "previous_owner_id": 1,   // roster_id of the previous owner
    "owner_id": 2             // roster_id of current owner
  },
  {
    "season": "2020",
    "round": 3,
    "roster_id": 2,
    "previous_owner_id": 2,
    "owner_id": 1
  },
  ...
]
```

### Get NFL state

```
GET https://api.sleeper.app/v1/state/<sport>
```

```shell
curl "https://api.sleeper.app/v1/state/nfl"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `sport` | `nfl`, `nba`, `lcs`, etc. |

Returns information about the current state for any sport.

Example response:

```javascript
{
  "week": 2,                          // week
  "season_type": "regular",           // pre, post, regular
  "season_start_date": "2020-09-10",  // regular season start
  "season": "2020",                   // current season
  "previous_season": "2019",
  "leg": 2,                           // week of regular season
  "league_season": "2021",            // active season for leagues
  "league_create_season": "2021",     // flips in December
  "display_week": 3                   // which week to display in UI, can differ from "week"
}
```

---

## Drafts

### Get all drafts for a user

```
GET https://api.sleeper.app/v1/user/<user_id>/drafts/<sport>/<season>
```

```shell
curl "https://api.sleeper.app/v1/user/<user_id>/drafts/nfl/2018"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `user_id` | The numerical ID of the user. |
| `sport` | Only `nfl` is currently supported. |
| `season` | Season, e.g. `2017`, `2018`, etc. |

Example response:

```javascript
[
  {
    "type": "snake",
    "status": "complete",
    "start_time": 1515700800000,
    "sport": "nfl",
    "settings": {
      "teams": 6,
      "slots_wr": 2,
      "slots_te": 1,
      "slots_rb": 2,
      "slots_qb": 1,
      "slots_k": 1,
      "slots_flex": 2,
      "slots_def": 1,
      "slots_bn": 5,
      "rounds": 15,
      "pick_timer": 120
    },
    "season_type": "regular",
    "season": "2017",
    "metadata": {
      "scoring_type": "ppr",
      "name": "My Dynasty",
      "description": ""
    },
    "league_id": "257270637750382592",
    "last_picked": 1515700871182,
    "last_message_time": 1515700942674,
    "last_message_id": "257272036450111488",
    "draft_order": null,
    "draft_id": "257270643320426496",
    "creators": null,
    "created": 1515700610526
  },
  ...
]
```

### Get all drafts for a league

```
GET https://api.sleeper.app/v1/league/<league_id>/drafts
```

```shell
curl "https://api.sleeper.app/v1/league/<league_id>/drafts"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `league_id` | The ID of the league to retrieve drafts for. |

A league can have multiple drafts, especially dynasty leagues — though most leagues will only have one. Drafts are sorted from most recent to earliest.

Response shape is the same as [Get all drafts for a user](#get-all-drafts-for-a-user) above.

### Get a specific draft

```
GET https://api.sleeper.app/v1/draft/<draft_id>
```

```shell
curl "https://api.sleeper.app/v1/draft/<draft_id>"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `draft_id` | The ID of the draft to retrieve. |

Example response:

```javascript
{
  "type": "snake",
  "status": "complete",
  "start_time": 1515700800000,
  "sport": "nfl",
  "settings": {
    "teams": 6,
    "slots_wr": 2,
    "slots_te": 1,
    "slots_rb": 2,
    "slots_qb": 1,
    "slots_k": 1,
    "slots_flex": 2,
    "slots_def": 1,
    "slots_bn": 5,
    "rounds": 15,
    "pick_timer": 120
  },
  "season_type": "regular",
  "season": "2017",
  "metadata": {
    "scoring_type": "ppr",
    "name": "My Dynasty",
    "description": ""
  },
  "league_id": "257270637750382592",
  "last_picked": 1515700871182,
  "last_message_time": 1515700942674,
  "last_message_id": "257272036450111488",

  // this is the user_id to draft slot mapping
  "draft_order": {
    "12345678": 1,
    "23434332": 2,
    ...
  },

  // this is the draft slot to roster_id mapping
  // leagues have rosters, which have roster_ids
  // this means draft slot 1 (column 1) will go to roster 10, slot 2 will go to roster_id 3, etc.
  "slot_to_roster_id": {
    "1": 10,
    "2": 3,
    "3": 5
  },

  "draft_id": "257270643320426496",
  "creators": null,
  "created": 1515700610526
}
```

### Get all picks in a draft

```
GET https://api.sleeper.app/v1/draft/<draft_id>/picks
```

```shell
curl "https://api.sleeper.app/v1/draft/<draft_id>/picks"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `draft_id` | The ID of the draft to retrieve picks for. |

Example response:

```javascript
[
  {
    "player_id": "2391",
    "picked_by": "234343434", // user_id this pick will go to (not all leagues have users in every slot, this can be "")
    "roster_id": "1",          // roster_id this pick will go to
    "round": 5,
    "draft_slot": 5,           // which column this is on the draft board
    "pick_no": 1,
    "metadata": {
      "team": "ARI",
      "status": "Injured Reserve",
      "sport": "nfl",
      "position": "RB",
      "player_id": "2391",
      "number": "31",
      "news_updated": "1513007102037",
      "last_name": "Johnson",
      "injury_status": "Out",
      "first_name": "David"
    },
    "is_keeper": null,
    "draft_id": "257270643320426496"
  },
  {
    "player_id": "1408",
    "picked_by": "234343434",
    "roster_id": "1",
    "round": 5,
    "draft_slot": 6,
    "pick_no": 2,
    "metadata": {
      "team": "PIT",
      "status": "Active",
      "sport": "nfl",
      "position": "RB",
      "player_id": "1408",
      "number": "26",
      "news_updated": "1515698101257",
      "last_name": "Bell",
      "injury_status": "",
      "first_name": "Le'Veon"
    },
    "is_keeper": null,
    "draft_id": "257270643320426496"
  },
  {
    "player_id": "536",
    "picked_by": "667279356739584",
    "pick_no": 3,
    "metadata": {
      "team": "PIT",
      "status": "Active",
      "sport": "nfl",
      "position": "WR",
      "player_id": "536",
      "number": "84",
      "news_updated": "1515673801292",
      "last_name": "Brown",
      "injury_status": "Probable",
      "first_name": "Antonio"
    },
    "is_keeper": null,
    "draft_id": "257270643320426496"
  },
  ...
]
```

### Get traded picks in a draft

```
GET https://api.sleeper.app/v1/draft/<draft_id>/traded_picks
```

```shell
curl "https://api.sleeper.app/v1/draft/<draft_id>/traded_picks"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `draft_id` | The ID of the draft to retrieve picks for. |

Retrieves all traded picks in a draft.

Example response:

```javascript
[
  {
    "season": "2019",
    "round": 5,               // which round the pick is
    "roster_id": 1,           // roster_id of ORIGINAL owner
    "previous_owner_id": 1,   // roster_id of the previous owner
    "owner_id": 2             // roster_id of current owner
  },
  {
    "season": "2019",
    "round": 3,               // which round the pick is
    "roster_id": 2,           // roster_id of original owner
    "previous_owner_id": 2,   // roster_id of previous owner
    "owner_id": 1             // roster_id of current owner
  },
  ...
]
```

---

## Players

### Fetch all players

```
GET https://api.sleeper.app/v1/players/<sport>?position=<position>&active=<true>
```

```shell
curl "https://api.sleeper.app/v1/players/nfl"
```

You can also filter by position, by active status, or both:

```shell
curl "https://api.sleeper.app/v1/players/nfl?position=QB"
curl "https://api.sleeper.app/v1/players/nfl?active=true"
curl "https://api.sleeper.app/v1/players/nfl?position=QB&active=true"
```

**Query Parameters**

| Parameter | Description |
|---|---|
| `position` | Only return players whose fantasy positions include this position, e.g. `QB` — optional. |
| `active` | Set to `true` to only return active players; any other value is ignored — optional. |

Both parameters can be used individually or combined. Filtered responses are much smaller than the full ~5MB player map, so they're a good fit if you only need a subset of players.

> **Important:** Please use this call sparingly — it's intended to be called at most once per day to keep your player IDs updated. The average response size is close to **5MB**. Rosters and draft picks reference `Player IDs` (like `"1042"`, `"2403"`, `"CAR"`), and the `/players` call provides the map to look up what those IDs mean. **Save this information on your own servers** rather than calling this endpoint repeatedly.

Example response:

```javascript
{
  "3086": {
    "hashtag": "#TomBrady-NFL-NE-12",
    "depth_chart_position": 1,
    "status": "Active",
    "sport": "nfl",
    "fantasy_positions": ["QB"],
    "number": 12,
    "search_last_name": "brady",
    "injury_start_date": null,
    "weight": "220",
    "position": "QB",
    "practice_participation": null,
    "sportradar_id": "",
    "team": "NE",
    "last_name": "Brady",
    "college": "Michigan",
    "fantasy_data_id": 17836,
    "injury_status": null,
    "player_id": "3086",
    "height": "6'4\"",
    "search_full_name": "tombrady",
    "age": 40,
    "stats_id": "",
    "birth_country": "United States",
    "espn_id": "",
    "search_rank": 24,
    "first_name": "Tom",
    "depth_chart_order": 1,
    "years_exp": 14,
    "rotowire_id": null,
    "rotoworld_id": 8356,
    "search_first_name": "tom",
    "yahoo_id": null
  },
  ...
}
```

### Trending Players

```
GET https://api.sleeper.app/v1/players/<sport>/trending/<type>?lookback_hours=<hours>&limit=<int>
```

```shell
curl "https://api.sleeper.app/v1/players/nfl/trending/add"
```

**URL Parameters**

| Parameter | Description |
|---|---|
| `sport` | The sport, e.g. `nfl`. |
| `type` | Either `add` or `drop`. |
| `lookback_hours` | Number of hours to look back (default is 24) — optional. |
| `limit` | Number of results you want (default is 25) — optional. |

Returns a list of trending players based on add/drop activity in the given lookback window.

Example response:

```javascript
[
  {
    "player_id": "1111", // the player_id
    "count": 45          // number of adds
  },
  ...
]
```

**Embeddable widget** — copy the code below to embed the trending list on your own app:

```html
<iframe src="https://sleeper.app/embed/players/nfl/trending/add?lookback_hours=24&limit=25" width="350" height="500" allowtransparency="true" frameborder="0"></iframe>
```

> **Note:** Please give attribution to Sleeper when using their trending data.

---

## Errors

The Sleeper API uses the following error codes:

| Code | Meaning |
|---|---|
| 400 | Bad Request — Your request is invalid. |
| 404 | Not Found — The specified resource could not be found. |
| 429 | Too Many Requests — You're requesting too much, too fast. Slow down. |
| 500 | Internal Server Error — There was a problem with the Sleeper server. Try again later. |
| 503 | Service Unavailable — Sleeper is temporarily offline for maintenance. Please try again later. |
