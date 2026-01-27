import csv
import pathlib

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


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
    return name.lower()


def _prepare_club_lookup(rosters: list[club_util.ClubInfo]) -> dict[str, str]:
    club_name_lookup = {
        _normalize_name(roster.club_name): roster.club_name for roster in rosters
    }
    if len(club_name_lookup) != len(rosters):
        raise RuntimeError("Non-unique club names")

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

    return club_name_lookup


def main() -> None:
    matches = _load_matches()
    print(len(matches))

    rosters = _load_rosters()
    club_name_lookup = _prepare_club_lookup(rosters)
    print(club_name_lookup)


if __name__ == "__main__":
    main()
