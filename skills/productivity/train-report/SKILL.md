---
name: train-report
description: NYC Subway train report — real-time ETA for a station (both directions). Takes a station name as argument and shows trains in both directions.
version: 3.1.0
author: hermclaw
dependencies:
  - uv
metadata:
  hermes:
    tags: [NYC, Subway, MTA, Transit, Realtime, Trains]
---

# NYC Subway Train Report

Real-time ETA for a subway station. Give it a station name and it shows trains in **both directions**.

## Usage

```bash
train-report "34 St-Penn Station"   # Full official name
train-report "Atlantic Av-Barclays Ctr"  # Abbreviated name (Av/Ctr)
train-report --list                 # See all available stations
```

### Fuzzy search

Case-insensitive partial matching, abbreviation aliases, and common nicknames all work:

```bash
train-report "penn station"         # nickname → 34 St-Penn Station
train-report "times square"         # nickname → Times Sq-42 St
train-report "bedford av"           # Av↔Ave↔Avenue aliases
train-report "canal st"             # St↔Street aliases
train-report "ditmars"              # partial match → Astoria-Ditmars Blvd
```

Ambiguous partial matches (e.g. `"14 st"`) list all candidates and ask you to be more specific.

## Example Output

```
🕐  12:15 PM — 34 St-Penn Station
══════════════════════════════════════════════════

⬆️  Uptown / Northbound
   (A / C / E)
   A → 207 St-Ovway                 [  2 min]  12:17
   E → Jamaica Center-Parsons/Archer [  5 min]  12:20
   C → 168 St                       [  9 min]  12:24

⬇️  Downtown / Southbound
   (A / C / E)
   A → Ozone Park-Lefferts Blvd     [  3 min]  12:18
   E → World Trade Center           [  7 min]  12:22
   C → Euclid Av                    [ 11 min]  12:26
```

## Available Stations

Run `train-report --list` to see all 788 station entries. The database covers **all 379 NYC subway stations** with both directional stop IDs, plus aliases (St/Street, Av/Ave/Avenue, common nicknames).

Common ones include:

| Brooklyn | Manhattan | Queens |
|----------|-----------|--------|
| Hoyt St | 34 St-Penn Station | Union Sq |
| Jay St-MetroTech | Times Sq-42 St | Jackson Hts-Roosevelt Av |
| Atlantic Av-Barclays Ctr | Grand Central-42 St | Forest Hills-71 Av |
| Borough Hall | 14 St-Union Sq | Jamaica Center-Parsons/Archer |
| Clark St | 96 St | Astoria-Ditmars Blvd |
| | Canal St | |

## Station Database

The `STATIONS` dict in the script contains **788 entries** covering all 379 NYC subway stations (both N/S directions) with aliases. It was auto-generated from the [MTA GTFS static data](https://web.mta.info/developers/data/nyct/subway/google_transit.zip).

### Regenerating the database

To refresh the station data from the latest MTA feed:
```bash
uv run --script /path/to/train-report/scripts/regenerate-stations.py /path/to/train-report/scripts/train-report
```

The regeneration script:
1. Downloads the latest GTFS zip from MTA
2. Parses `stops.txt`, `trips.txt`, `stop_times.txt` to build station→lines mapping
3. Groups stops by parent station, separates N/S directions
4. Generates aliases (St↔Street, Av↔Ave↔Avenue, common nicknames)
5. Writes the updated `STATIONS` dict into the train-report script

### Pitfalls

- **MTA uses parent/child stop hierarchy**: Each station has a parent (no direction), then N and S child stops. Only include stations where both N and S exist.
- **Express variants**: Lines like `6X`, `7X` should be filtered out of display — keep the local variant.
- **"St" vs "Station"**: Use word-boundary regex when replacing St→Street to avoid mangling names like "Penn Station" into "Penn Streetation".
- **Multiple stops per station**: Some stations serve multiple lines (e.g., 14 St has 1/2/3 AND A/C/E). The GTFS data captures all lines that serve each stop.
- **Stop ID format**: MTA uses pattern like `233N`, `233S` where the suffix indicates direction. This mapping is consistent across all lines.
