#!/usr/bin/env -S uv run --python 3.11
# /// script
# requires-python = ">=3.11"
# dependencies = ["standard-library-only"]
# ///
"""
Regenerate the STATIONS dict in train-report script from MTA GTFS static data.

Usage:
  uv run --script scripts/regenerate-stations.py [path/to/train-report]

Downloads the latest MTA GTFS static data, extracts all stations with both
N/S stop IDs, generates aliases, and writes the updated STATIONS dict into
the train-report script.
"""

import sys
import urllib.request
import zipfile
import io
import csv
import re
import os
from collections import defaultdict
from pathlib import Path


GTFS_URL = "https://web.mta.info/developers/data/nyct/subway/google_transit.zip"


def fetch_gtfs():
    """Download and parse MTA GTFS static data."""
    print(f"Downloading MTA GTFS from {GTFS_URL}...")
    response = urllib.request.urlopen(GTFS_URL)
    data = response.read()
    print(f"Downloaded {len(data):,} bytes")

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        with z.open('stops.txt') as f:
            stops = {row['stop_id']: row for row in csv.DictReader(io.TextIOWrapper(f, 'utf-8'))}

        with z.open('trips.txt') as f:
            trips = {row['trip_id']: row for row in csv.DictReader(io.TextIOWrapper(f, 'utf-8'))}

        with z.open('stop_times.txt') as f:
            stop_to_lines = defaultdict(set)
            for row in csv.DictReader(io.TextIOWrapper(f, 'utf-8')):
                trip = trips.get(row['trip_id'])
                if trip:
                    stop_to_lines[row['stop_id']].add(trip['route_id'])

    return stops, stop_to_lines


def build_stations(stops, stop_to_lines):
    """Build station dict with aliases from GTFS data."""
    # Group stops by parent station
    station_data = defaultdict(lambda: {'N': None, 'S': None, 'lines': set()})

    for stop_id, stop in stops.items():
        parent_id = stop.get('parent_station', '')
        if not parent_id:
            continue
        parent = stops.get(parent_id)
        if not parent:
            continue

        name = parent['stop_name']
        lines = stop_to_lines.get(stop_id, set())

        if stop_id.endswith('N'):
            station_data[name]['N'] = stop_id
            station_data[name]['lines'].update(lines)
        elif stop_id.endswith('S'):
            station_data[name]['S'] = stop_id
            station_data[name]['lines'].update(lines)

    # Build final dict with aliases
    stations = {}
    for name, data in station_data.items():
        if not data['N'] or not data['S'] or not data['lines']:
            continue

        lines = sorted(data['lines'])
        # Remove express variants for display
        display_lines = [l for l in lines if not l.endswith('X')]
        if not display_lines:
            display_lines = lines

        key = name.lower()
        stations[key] = (data['N'], data['S'], display_lines)

        # Generate aliases
        aliases = set()

        # St ↔ Street (but not when followed by "station")
        st_pattern = r'\bst\b(?!.*station)'
        street_pattern = r'\bstreet\b(?!.*station)'
        if re.search(st_pattern, key):
            aliases.add(re.sub(st_pattern, 'street', key))
        if re.search(street_pattern, key):
            aliases.add(re.sub(street_pattern, 'st', key))

        # Sts ↔ Streets
        if ' sts' in key:
            aliases.add(key.replace(' sts', ' streets'))
        if ' streets' in key:
            aliases.add(key.replace(' streets', ' sts'))

        # Av ↔ Ave ↔ Avenue (word boundary)
        parts = key.split()
        for i, part in enumerate(parts):
            if part == 'av':
                new = parts.copy()
                new[i] = 'ave'
                aliases.add(' '.join(new))
                new[i] = 'avenue'
                aliases.add(' '.join(new))
            if part == 'ave':
                new = parts.copy()
                new[i] = 'av'
                aliases.add(' '.join(new))
                new[i] = 'avenue'
                aliases.add(' '.join(new))
            if part == 'avenue':
                new = parts.copy()
                new[i] = 'av'
                aliases.add(' '.join(new))
                new[i] = 'ave'
                aliases.add(' '.join(new))

        # Special nicknames
        special = {
            '34 st-penn station': ['penn station', '34 st', '34th st'],
            '34 st-herald sq': ['herald square'],
            '14 st-union sq': ['union sq', 'union square'],
            'hoyt st': ['hoyt street'],
            'clark st': ['clark street'],
            'high st': ['high street'],
            'jay st-metrotech': ['jay st', 'jay street', 'metrotech'],
            'times sq-42 st': ['times sq', 'times square', '42 st', '42nd st'],
            'grand central-42 st': ['grand central', '42 st', '42nd st'],
            'canal st': ['canal street'],
            'w 4 st-wash sq': ['w 4 st', 'w 4th st', 'west 4 st', 'west 4th st', 'washington sq'],
            'w 8 st-ny aquarium': ['w 8 st', 'west 8 st'],
            'dekalb av': ['dekalb ave', 'dekalb avenue'],
            'atlantic av-barclays ctr': ['atlantic av', 'atlantic ave', 'barclays ctr', 'barclays center'],
            'hoyt-schermerhorn streets': ['hoyt-schermerhorn sts'],
            'wtc cortlandt': ['wtc'],
            'world trade center': ['wtc'],
            '42 st-port authority bus terminal': ['port authority', '42 st-port authority'],
            '42 st-bryant pk': ['bryant park'],
            '72 st': ['72nd st'],
            '96 st': ['96th st'],
            '103 st': ['103rd st'],
            '110 st': ['110th st'],
            '116 st': ['116th st'],
        }
        if key in special:
            aliases.update(special[key])

        for alias in aliases:
            if alias not in stations:
                stations[alias] = (data['N'], data['S'], display_lines)

    return stations


def generate_stations_code(stations):
    """Generate Python code for the STATIONS dict."""
    code = '# Auto-generated from MTA GTFS static data (date)\n'
    code += '# Source: https://web.mta.info/developers/data/nyct/subway/google_transit.zip\n'
    code += f'# 379 stations with N/S pairs + aliases = {len(stations)} entries\n'
    code += '# Station name -> (northbound_stop_id, southbound_stop_id, lines)\n'
    code += 'STATIONS = {\n'

    for name in sorted(stations.keys()):
        north, south, lines = stations[name]
        lines_str = ', '.join(f'"{l}"' for l in lines)
        code += f'    "{name}": ("{north}", "{south}", [{lines_str}]),\n'

    code += '}\n'
    return code


def update_train_report_script(stations_code: str, script_path: str):
    """Update the STATIONS dict in the train-report script."""
    with open(script_path) as f:
        content = f.read()

    # Find the start of STATIONS = {
    start_marker = 'STATIONS = {'
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print(f"ERROR: Could not find '{start_marker}' in {script_path}")
        sys.exit(1)

    # Find the end: the closing brace before the next def
    # Look for the pattern: }

def
    rest = content[start_pos + len(start_marker):]
    depth = 1
    end_pos = 0
    for i, ch in enumerate(rest):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end_pos = i
                break

    # Extract just the dict body from the new code (skip header comments and STATIONS = { prefix)
    new_body_start = stations_code.find('STATIONS = {') + len('STATIONS = {')
    new_body_end = stations_code.rfind('}')
    new_body = stations_code[new_body_start:new_body_end].strip()

    # Reconstruct the script
    header = content[:start_pos + len(start_marker)]
    footer = content[start_pos + len(start_marker) + end_pos + 1:]  # after the }

    updated = header + '\n' + new_body + '\n' + footer

    with open(script_path, 'w') as f:
        f.write(updated)


def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else None
    skill_dir = Path(__file__).parent.parent

    if script_path is None:
        # Default: look for train-report script in sibling dir or cwd
        candidates = [
            skill_dir / 'scripts' / 'train-report',
            Path.cwd() / 'train-report',
            Path.home() / '.hermes-openrouter' / 'skills' / 'productivity' / 'train-report' / 'scripts' / 'train-report',
        ]
        for c in candidates:
            if c.exists():
                script_path = str(c)
                break
        if script_path is None:
            print("Usage: uv run --script scripts/regenerate-stations.py [path/to/train-report]")
            sys.exit(1)

    stations, stop_to_lines = fetch_gtfs()
    stations_dict = build_stations(stops, stop_to_lines)

    print(f"\nFound {len([s for s in station_data.values() if s['N'] and s['S']])} stations with both directions")
    print(f"Generated {len(stations_dict)} entries with aliases")

    stations_code = generate_stations_code(stations_dict)

    # Show some sample entries
    print("\nSample entries:")
    for key in ['hoyt st', 'penn station', 'times sq', 'union sq']:
        if key in stations_dict:
            print(f"  {key}: {stations_dict[key]}")

    update_train_report_script(stations_code, script_path)
    print(f"\nUpdated {script_path}")


if __name__ == '__main__':
    main()
