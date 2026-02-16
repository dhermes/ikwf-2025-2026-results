import csv
import pathlib
import re

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIMPLE_NAME = re.compile(r"^[a-z0-9 ]+$")
_FALSE_DUPLICATE_CARDINAL = frozenset(
    ["Cardinals Wrestling Club", "Arlington Cardinals Wrestling Club"]
)
# NOTE: The `custom-normalized-team-names.json` are wrong for some clubs that
#       have very similar names.
_EXPLICIT_MAPPING: dict[str, dict[str, str]] = {
    "Litchfield `Rumble In the Jungle` 2026": {
        "STCWC": "Out of State - Missouri",
    },
    "THE Midwest Classic 2026": {
        "HoneyBadger WC": "Team HoneyBadger WC",
    },
    "Crushing Christmas Classic-Coal City": {
        "Team Honey Badger WC": "Team HoneyBadger WC",
    },
    "2026 Girls Rule Rumble": {
        "DC Wrestling ": "DC Wrestling Club",
        "Team Honey Badger WC": "Team HoneyBadger WC",
    },
    "Tots Bash": {
        "CWC": "Collinsville Wrestling Club",
    },
    "2025 Rocket Blast": {
        "CWC": "Champaign Wrestling Club",
    },
    "Spartan Rumble": {
        "CWC": "Champaign Wrestling Club",
    },
    "2026 O`Fallon Panther Pummel w/Girls": {
        "Fox WC": "Out of State - Missouri",
        "Camdenton WC": "Out of State - Missouri",
        "St. Charles WC": "Out of State - Missouri",
    },
    "2026 BRONCO INVITE": {
        "Spartans": "Spartan Wrestling Club",
    },
    "Cumberland Kids Heartbreak Havoc": {
        "Vincennes Grapplers Wrestling": "Out of State - Indiana",
    },
    "Daisy Fresh Wrestling Open": {
        "Evansville Reitz": "Out of State - Indiana",
    },
    "Olympia Spartan Showdown": {
        "Backyard Brawlers": "Backyard Brawlers Midwest WC",
    },
}

# NOTE: `_OVERRIDE_TEAM_MAPPING` provides tournament specific overrides for a
#       given team name. For now this is just to support the fact that
#       St. Charles, IL and St. Charles, MO have the same team name. But the
#       one from Missouri only goes to tournaments near St. Louis.
_OVERRIDE_TEAM_MAPPING: dict[str, dict[str, str]] = {
    "Devils Gauntlet Battle for the Belts": {
        "St. Charles WC": "Out of State - Missouri"
    },
    "42nd Annual Bulls Wrestling Tournament": {
        "St. Charles Wrestling Club": "Out of State - Missouri"
    },
    "Granite City Kids Holiday Classic": {
        "St. Charles Wrestling Club": "Out of State - Missouri"
    },
    "2025 O`Fallon Beginners/Girls Open": {"STCWC": "Out of State - Missouri"},
    "Highland Howl Jarron Haberer memorial": {"STCWC": "Out of State - Missouri"},
    "Roxana Rumble": {"STCWC": "Out of State - Missouri"},
}


def _load_matches() -> list[bracket_util.MatchV1]:
    input_file = _ROOT / "_parsed-data" / "all-matches-01.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["Division"] == "":
            row["Division"] = None

    matches_root = bracket_util.MatchesV1.model_validate(rows)
    return matches_root.root


def _normalize_name(name: str) -> str:
    case_insensitive = name.lower()

    parts = case_insensitive.split()
    whitespace_normalized = " ".join(parts)

    without_punctuation = whitespace_normalized.replace("'", "")
    without_punctuation = without_punctuation.replace(".", "")
    without_punctuation = without_punctuation.replace(",", "")
    without_punctuation = without_punctuation.replace("&", "and")
    without_punctuation = without_punctuation.replace("-", " ")
    without_punctuation = without_punctuation.replace("`", "")
    # NOTE: `c/ ` is a special case based on a likely typo in real data
    without_punctuation = without_punctuation.replace("c/ ", "c ")

    without_punctuation = without_punctuation.replace(" (", " ")
    without_punctuation = without_punctuation.replace(") ", " ")
    without_punctuation = without_punctuation.replace(" / ", " ")
    if without_punctuation.startswith("("):
        without_punctuation = without_punctuation[1:]
    if without_punctuation.endswith(")"):
        without_punctuation = without_punctuation[:-1]

    if without_punctuation == "rick larsen wrestling club(ind":
        return "rick larsen wrestling club ind"

    if _SIMPLE_NAME.match(without_punctuation) is None:
        raise RuntimeError("Unhandled name needs normalized", name, without_punctuation)

    parts = without_punctuation.split()
    whitespace_normalized = " ".join(parts)

    return whitespace_normalized


def _prepare_club_lookup(rosters: list[club_util.ClubInfo]) -> dict[str, str]:
    club_name_lookup = {
        _normalize_name(roster.club_name): roster.club_name for roster in rosters
    }
    if len(club_name_lookup) != len(rosters):
        raise RuntimeError("Non-unique club names")

    # First pass: WC and "Wrestling Club" synonym
    keys = sorted(club_name_lookup.keys())
    for key in keys:
        new_key = None
        if "wrestling club" in key:
            new_key = key.replace("wrestling club", "wc")
        elif key.endswith(" wc"):
            new_key = key[:-2] + "wrestling club"

        if new_key is None:
            continue

        if new_key in club_name_lookup:
            raise ValueError("Unexpected collision", key, new_key)
        club_name_lookup[new_key] = club_name_lookup[key]

    # Second pass: Jr. and "Junior" synonym
    keys = sorted(club_name_lookup.keys())
    for key in keys:
        new_key = None
        if " jr " in key:
            new_key = key.replace(" jr ", " junior ")
        elif key.startswith("jr "):
            new_key = "junior" + key[2:]
        elif " junior " in key:
            new_key = key.replace(" junior ", " jr ")
        elif key.startswith("junior "):
            new_key = "jr" + key[6:]

        if new_key is None:
            continue

        if new_key in club_name_lookup:
            raise ValueError("Unexpected collision", key, new_key)
        club_name_lookup[new_key] = club_name_lookup[key]

    return club_name_lookup


def _lookup_team(
    team: str,
    event_name: str,
    club_name_lookup: dict[str, str],
    custom_team_name_map: dict[str, str],
) -> str:
    if team == "":
        return ""

    explicit_value = _EXPLICIT_MAPPING.get(event_name, {}).get(team)
    if explicit_value is not None:
        return explicit_value

    event_override = _OVERRIDE_TEAM_MAPPING.get(event_name, {})
    mapped_override = event_override.get(team)
    if mapped_override is not None:
        return mapped_override

    team_normalized = _normalize_name(team)
    matched = club_name_lookup.get(team_normalized)
    if matched is not None:
        return matched

    partial_matches = {
        value for key, value in club_name_lookup.items() if key in team_normalized
    }
    if len(partial_matches) == 1:
        return list(partial_matches)[0]

    if partial_matches == set(_FALSE_DUPLICATE_CARDINAL):
        return "Arlington Cardinals Wrestling Club"

    if len(partial_matches) > 1:
        raise RuntimeError("Unexpected duplicates", team, partial_matches)

    custom_match = custom_team_name_map.get(team_normalized)
    if custom_match is not None:
        return custom_match

    raise RuntimeError("Could not match team", team, team_normalized, event_name)


def _lookup_teams(
    match_: bracket_util.MatchV1,
    club_name_lookup: dict[str, str],
    custom_team_name_map: dict[str, str],
) -> tuple[str, str]:
    winner_team_matched = _lookup_team(
        match_.winner_team, match_.event_name, club_name_lookup, custom_team_name_map
    )
    loser_team_matched = _lookup_team(
        match_.loser_team, match_.event_name, club_name_lookup, custom_team_name_map
    )
    return winner_team_matched, loser_team_matched


def main() -> None:
    matches_v1 = _load_matches()

    rosters = club_util.load_rosters()
    club_name_lookup = _prepare_club_lookup(rosters)
    custom_team_name_map = club_util.load_custom_team_name_map()

    matches_v2: list[bracket_util.MatchV2] = []
    for match_ in matches_v1:
        normalized = _lookup_teams(match_, club_name_lookup, custom_team_name_map)
        winner_team_normalized, loser_team_normalized = normalized
        matches_v2.append(
            bracket_util.MatchV2.from_v1(
                match_, winner_team_normalized, loser_team_normalized
            )
        )

    matches_file_v2 = _ROOT / "_parsed-data" / "all-matches-02.csv"
    with open(matches_file_v2, "w") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=bracket_util.CSV_FIELD_NAMES_V2)
        writer.writeheader()
        for match_ in matches_v2:
            writer.writerow(match_.model_dump(mode="json", by_alias=True))


if __name__ == "__main__":
    main()
