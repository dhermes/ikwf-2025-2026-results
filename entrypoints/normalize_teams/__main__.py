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


def _load_matches() -> list[bracket_util.Match]:
    input_file = _ROOT / "_parsed-data" / "all-matches-01.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["Division"] == "":
            row["Division"] = None

    matches_root = bracket_util.Matches.model_validate(rows)
    return matches_root.root


def _load_rosters() -> list[club_util.ClubInfo]:
    input_file = _ROOT / "_parsed-data" / "rosters.json"
    with open(input_file) as file_obj:
        as_json = file_obj.read()

    clubs_root = club_util.Clubs.model_validate_json(as_json)
    return clubs_root.root


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


def _lookup_team(team: str, club_name_lookup: dict[str, str]) -> str | None:
    if team == "":
        return None

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

    return None


def _lookup_teams(
    match: bracket_util.Match, club_name_lookup: dict[str, str]
) -> tuple[str | None, str | None]:
    winner_team_matched = _lookup_team(match.winner_team, club_name_lookup)
    loser_team_matched = _lookup_team(match.loser_team, club_name_lookup)
    return winner_team_matched, loser_team_matched


def main() -> None:
    matches = _load_matches()
    print(len(matches))

    rosters = _load_rosters()
    club_name_lookup = _prepare_club_lookup(rosters)

    for match in matches:
        _lookup_teams(match, club_name_lookup)


if __name__ == "__main__":
    main()
