import csv
import pathlib
import re

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SIMPLE_NAME = re.compile(r"^[a-z0-9 ]+$")


def _load_matches() -> list[bracket_util.MatchV2]:
    input_file = _ROOT / "_parsed-data" / "all-matches-02.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["Division"] == "":
            row["Division"] = None

    matches_root = bracket_util.MatchesV2.model_validate(rows)
    return matches_root.root


def _normalize_name(name: str) -> str:
    case_insensitive = name.lower()

    parts = case_insensitive.split()
    whitespace_normalized = " ".join(parts)

    without_punctuation = whitespace_normalized.replace("'", "")
    without_punctuation = without_punctuation.replace('"', "")
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


def _prepare_athlete_lookup(
    rosters: list[club_util.ClubInfo],
) -> dict[str, dict[str, club_util.Athlete]]:
    roster_map: dict[str, dict[str, club_util.Athlete]] = {}
    for roster in rosters:
        athlete_map: dict[str, club_util.Athlete] = {}
        for athlete in roster.athletes:
            normalized_name = _normalize_name(athlete.name)
            if normalized_name in athlete_map:
                raise RuntimeError(
                    "Unexpected duplicate",
                    normalized_name,
                    athlete,
                    athlete_map[normalized_name],
                )

            athlete_map[normalized_name] = athlete

        if roster.club_name in roster_map:
            raise RuntimeError("Unexpected duplicate", roster.club_name)

        roster_map[roster.club_name] = athlete_map

    return roster_map


def main() -> None:
    matches_v2 = _load_matches()
    print(len(matches_v2))
    rosters = club_util.load_rosters()
    athlete_lookup = _prepare_athlete_lookup(rosters)
    print(len(athlete_lookup))


if __name__ == "__main__":
    main()
