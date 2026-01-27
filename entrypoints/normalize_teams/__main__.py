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


def main() -> None:
    matches = _load_matches()
    print(len(matches))
    rosters = _load_rosters()
    print(len(rosters))


if __name__ == "__main__":
    main()
