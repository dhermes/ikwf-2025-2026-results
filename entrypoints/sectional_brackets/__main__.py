import csv
import pathlib

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_NULLABLE_KEYS = (
    "Division",
    "Winner (normalized)",
    "Winner USAW Number",
    "Winner IKWF Age",
    "Winner weight",
    "Loser (normalized)",
    "Loser USAW Number",
    "Loser IKWF Age",
    "Loser weight",
)


def _load_matches() -> list[bracket_util.MatchV4]:
    input_file = _ROOT / "_parsed-data" / "all-matches-04.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        for key in _NULLABLE_KEYS:
            if row[key] == "":
                row[key] = None

    matches_root = bracket_util.MatchesV4.model_validate(rows)
    return matches_root.root


def _map_by_team(
    matches: list[bracket_util.MatchV4],
    team_names: set[str],
) -> dict[str, dict[str, list[bracket_util.MatchV4]]]:
    """Map first by team and then by USAW"""
    team_mapped: dict[str, dict[str, list[bracket_util.MatchV4]]] = {}

    for match_ in matches:
        winner_team = match_.winner_team_normalized
        winner_usaw_number = match_.winner_usaw_number
        if winner_team in team_names and winner_usaw_number is not None:
            by_athlete = team_mapped.setdefault(winner_team, {}).setdefault(
                winner_usaw_number, []
            )
            by_athlete.append(match_)

        loser_team = match_.loser_team_normalized
        loser_usaw_number = match_.loser_usaw_number
        if loser_team in team_names and loser_usaw_number is not None:
            by_athlete = team_mapped.setdefault(loser_team, {}).setdefault(
                loser_usaw_number, []
            )
            by_athlete.append(match_)

    return team_mapped


def main() -> None:
    sectional: club_util.Sectional = "West Chicago"  # TODO: Convert this to a flag
    matches_v4 = _load_matches()
    rosters = club_util.load_rosters()
    teams_in_sectional = [roster for roster in rosters if roster.sectional == sectional]
    team_names = set([roster.club_name for roster in teams_in_sectional])

    relevant_matches = [
        match_
        for match_ in matches_v4
        if (
            match_.winner_team_normalized in team_names
            or match_.loser_team_normalized in team_names
        )
    ]
    team_mapped = _map_by_team(relevant_matches, team_names)
    print(len(team_mapped))


if __name__ == "__main__":
    main()
