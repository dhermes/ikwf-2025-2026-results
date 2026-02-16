import csv
import datetime
import io
import pathlib

import openpyxl
import pydantic

import bracket_util
import club_util
import projection

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class _WeightAthlete(_ForbidExtra):
    usaw_number: str
    name: str
    ikwf_age: int
    team: str
    most_recent_weigh_in: datetime.date
    most_recent_weight: float
    projected_weight: float
    wins: pydantic.NonNegativeInt
    losses: pydantic.NonNegativeInt
    matches: list[bracket_util.MatchV4]
    state_2025_note: str


class _WeightClass(_ForbidExtra):
    athletes: list[_WeightAthlete]
    head_to_heads: list[bracket_util.MatchV4]


def _add_wrestler(
    team: str,
    key: tuple[bracket_util.Division, int],
    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass],
    athlete: club_util.Athlete,
    matches: list[bracket_util.MatchV4],
    most_recent_weigh_in: datetime.date,
    most_recent_weight: float,
    projected_weight: float,
    state_2025_note: str,
) -> None:
    if key not in weight_classes:
        weight_classes[key] = _WeightClass(athletes=[], head_to_heads=[])

    weight_class = weight_classes[key]
    existing_usaw = set(
        [other_athlete.usaw_number for other_athlete in weight_class.athletes]
    )

    usaw_number = athlete.usaw_number
    wins = 0
    losses = 0
    for match_ in matches:
        if match_.winner_usaw_number == usaw_number:
            wins += 1
            if match_.loser_usaw_number in existing_usaw:
                weight_class.head_to_heads.append(match_)
        elif match_.loser_usaw_number == usaw_number:
            losses += 1
            if match_.winner_usaw_number in existing_usaw:
                weight_class.head_to_heads.append(match_)
        else:
            raise RuntimeError("Unexpected match", match_, usaw_number)

    weight_class.athletes.append(
        _WeightAthlete(
            usaw_number=athlete.usaw_number,
            name=athlete.name,
            ikwf_age=athlete.ikwf_age,
            team=team,
            most_recent_weigh_in=most_recent_weigh_in,
            most_recent_weight=most_recent_weight,
            projected_weight=projected_weight,
            wins=wins,
            losses=losses,
            matches=matches,
            state_2025_note=state_2025_note,
        )
    )


def _sort_helper(athlete: _WeightAthlete) -> float:
    wins = athlete.wins
    losses = athlete.losses

    matches = wins + losses

    # NOTE: Assume a previous record of 5-5 to penalize low match counts while
    #       not materially changing the sorting of 16-5 vs. 12-8
    return (wins + 5) / (matches + 10)


def _sort_by_record(athletes: list[_WeightAthlete]) -> list[_WeightAthlete]:
    return sorted(athletes, key=_sort_helper, reverse=True)


def _make_csv(weight_class: _WeightClass) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ATHLETES"])
    writer.writerow(
        [
            "Name",
            "Wins",
            "Losses",
            "IKWF age",
            "USAW number",
            "Team",
            "State (2025)",
            "Winning percentage",
            "Adjusted score",
            "Most recent weigh-in",
            "Most recent weight",
            "Projected weight",
        ]
    )
    athletes = _sort_by_record(weight_class.athletes)
    for athlete in athletes:
        winning_percentage = athlete.wins / (athlete.wins + athlete.losses)
        adjusted_score = _sort_helper(athlete)

        row = [
            athlete.name,
            str(athlete.wins),
            str(athlete.losses),
            str(athlete.ikwf_age),
            athlete.usaw_number,
            athlete.team,
            athlete.state_2025_note,
            f"{winning_percentage:.3f}",
            f"{adjusted_score:.3f}",
            str(athlete.most_recent_weigh_in),
            f"{athlete.most_recent_weight:.1f}",
            f"{athlete.projected_weight:.1f}",
        ]
        writer.writerow(row)

    writer.writerow([])
    writer.writerow([])
    writer.writerow(["HEAD TO HEADS"])
    writer.writerow(["Winner", "Winner team", "Loser", "Loser team", "Result"])

    for match_ in weight_class.head_to_heads:
        row = [
            match_.winner_normalized,
            match_.winner_team_normalized,
            match_.loser_normalized,
            match_.loser_team_normalized,
            match_.result,
        ]
        writer.writerow(row)

    csv_string = output.getvalue()
    output.close()
    return csv_string


def _weight_class_sort_func(key: tuple[bracket_util.Division, int]) -> tuple[int, int]:
    division, weight = key
    return bracket_util.sortable_division(division), weight


def _generate_sectional_file(
    sectional: club_util.Sectional,
    matches_v4: list[bracket_util.MatchV4],
    rosters: list[club_util.ClubInfo],
    state_qualifiers: dict[str, dict[str, club_util.StateQualifier]],
) -> None:
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
    team_mapped = projection.map_by_team(relevant_matches, team_names)

    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass] = {}
    for team, by_usaw in team_mapped.items():
        (athletes,) = [
            roster.athletes for roster in teams_in_sectional if roster.club_name == team
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

            key, most_recent_weigh_in, most_recent_weight, projected_weight = (
                weight_class_info
            )

            state_2025_note = ""
            state_qualifier = state_qualifiers.get(team, {}).get(athlete.name)
            if state_qualifier is not None:
                state_2025_note = state_qualifier.result

            _add_wrestler(
                team,
                key,
                weight_classes,
                athlete,
                matches,
                most_recent_weigh_in,
                most_recent_weight,
                projected_weight,
                state_2025_note,
            )

    keys = sorted(weight_classes.keys(), key=_weight_class_sort_func)
    sheets: dict[str, str] = {}
    for key in keys:
        key_display = projection.display_weight_class(key)
        weight_class = weight_classes[key]
        if key_display in sheets:
            raise TypeError("Key appears more than once", key_display)
        sheets[key_display] = _make_csv(weight_class)

    stem = bracket_util.to_kebab_case(sectional)
    xslx_filename = _ROOT / "_parsed-data" / f"{stem}.xlsx"

    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)

    for sheet_name, csv_text in sheets.items():
        if len(sheet_name) > 31:
            raise RuntimeError("Sheet name too big for Excel", sheet_name)

        worksheet = workbook.create_sheet(title=sheet_name)
        reader = csv.reader(io.StringIO(csv_text))
        for row in reader:
            worksheet.append(row)

    workbook.save(xslx_filename)


def main() -> None:
    matches_v4 = projection.load_matches_v4()
    rosters = club_util.load_rosters()
    state_qualifiers = club_util.load_state_qualifiers()

    sectionals: tuple[club_util.Sectional, ...] = (
        "Central Chicago",
        "Central",
        "North Chicago",
        "North",
        "South Chicago",
        "South",
        "West Chicago",
        "West",
    )
    for sectional in sectionals:
        _generate_sectional_file(sectional, matches_v4, rosters, state_qualifiers)


if __name__ == "__main__":
    main()
