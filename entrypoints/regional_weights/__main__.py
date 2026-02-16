import pathlib

import openpyxl

import bracket_util
import club_util
import projection

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


_Entry = tuple[str, str, int, str, bracket_util.Division | None, int | None]


def _entry_sort_key(entry: _Entry) -> tuple[int, int, str, str, str]:
    team, name, _, usaw_number, division, weight = entry
    weight_int = 999 if weight is None else weight
    division_int = 999 if division is None else bracket_util.division_value(division)

    return division_int, weight_int, name, team, usaw_number


def _generate_regional_entries(
    teams: list[str],
    matches_v4: list[bracket_util.MatchV4],
    rosters: list[club_util.ClubInfo],
) -> list[_Entry]:
    team_names = set(teams)
    teams_in_regional = [roster for roster in rosters if roster.club_name in team_names]

    relevant_matches = [
        match_
        for match_ in matches_v4
        if (
            match_.winner_team_normalized in team_names
            or match_.loser_team_normalized in team_names
        )
    ]
    team_mapped = projection.map_by_team(relevant_matches, team_names)

    weight_by_usaw: dict[str, tuple[bracket_util.Division, int]] = {}
    for team, by_usaw in team_mapped.items():
        (athletes,) = [
            roster.athletes for roster in teams_in_regional if roster.club_name == team
        ]
        for usaw_number, matches in by_usaw.items():
            (athlete,) = [
                athlete for athlete in athletes if athlete.usaw_number == usaw_number
            ]
            weight_class_info = projection.determine_weight_class(
                usaw_number, athlete.ikwf_age, matches
            )
            if weight_class_info is None:
                continue

            key, _, _, _ = weight_class_info
            division, weight = key
            if athlete.usaw_number in weight_by_usaw:
                raise KeyError("Athlete already mapped", athlete.usaw_number)
            weight_by_usaw[athlete.usaw_number] = division, weight

    all_entries: list[_Entry] = []
    for roster in teams_in_regional:
        team = roster.club_name
        for athlete in roster.athletes:
            ikwf_age = athlete.ikwf_age
            usaw_number = athlete.usaw_number
            name = athlete.name

            division = None
            weight = None
            if usaw_number in weight_by_usaw:
                division, weight = weight_by_usaw[usaw_number]

            all_entries.append((team, name, ikwf_age, usaw_number, division, weight))

    all_entries.sort(key=_entry_sort_key)
    return all_entries


def main() -> None:
    matches_v4 = projection.load_matches_v4()
    rosters = club_util.load_rosters()
    regional_assignments = projection.get_regional_assignments()

    by_regional: dict[str, list[_Entry]] = {}
    for name, teams in regional_assignments.items():
        _, location = name.split(" :: ")
        if location == "No Regional":
            continue
        entries = _generate_regional_entries(teams, matches_v4, rosters)
        if name in by_regional:
            raise KeyError("Repeat regional", name)
        by_regional[name] = entries

    xslx_filename = _ROOT / "_parsed-data" / "regional-weight-classes.xlsx"

    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)

    for name, entries in by_regional.items():
        sheet_name = name.replace(" :: ", " - ")
        if len(sheet_name) > 31:
            raise RuntimeError(
                "Sheet name too big for Excel", len(sheet_name), sheet_name
            )

        worksheet = workbook.create_sheet(title=sheet_name)
        worksheet.append(
            (
                "Team",
                "Name",
                "IKWF age",
                "USAW Number",
                "Projected division",
                "Projected weight class",
                "Actual division",
                "Actual weight class",
            )
        )
        for entry in entries:
            team, name, ikwf_age, usaw_number, division, weight = entry
            division_str = (
                "" if division is None else projection.display_division(division)
            )
            worksheet.append(
                (team, name, ikwf_age, usaw_number, division_str, weight, "", "")
            )

    workbook.save(xslx_filename)


if __name__ == "__main__":
    main()
