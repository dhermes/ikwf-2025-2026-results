import argparse
import csv
import io

import openpyxl
import pydantic

import bracket_util
import club_util
import projection

_NULLABLE_KEYS = (
    "Projected division",
    "Projected weight class",
    "Actual division",
    "Actual weight class",
)


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class _Entry(_ForbidExtra):
    unused1: str = pydantic.Field(alias="Team")
    unused2: str = pydantic.Field(alias="Name")
    unused3: str = pydantic.Field(alias="IKWF age")
    usaw_number: str = pydantic.Field(alias="USAW Number")
    unused4: str | None = pydantic.Field(alias="Projected division")
    unused5: int | None = pydantic.Field(alias="Projected weight class")
    actual_division: str | None = pydantic.Field(alias="Actual division")
    actual_weight_class: int | None = pydantic.Field(alias="Actual weight class")


class _Entries(pydantic.RootModel[list[_Entry]]):
    pass


def _get_filenames() -> tuple[str, str]:
    parser = argparse.ArgumentParser(description="Produce a regional seeding sheet")
    parser.add_argument("--entries-filename", required=True, dest="entries_filename")
    parser.add_argument("--seeding-filename", required=True, dest="seeding_filename")
    args = parser.parse_args()

    return args.entries_filename, args.seeding_filename


def _load_entries(entries_filename: str) -> list[_Entry]:
    with open(entries_filename) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        for key in _NULLABLE_KEYS:
            if row[key] == "":
                row[key] = None

    entries_root = _Entries.model_validate(rows)
    return entries_root.root


def _preprocess_entries(
    entries: list[_Entry],
) -> tuple[set[str], dict[tuple[bracket_util.Division, int], list[str]]]:
    all_usaw_numbers: set[str] = set()
    weight_classes: dict[tuple[bracket_util.Division, int], list[str]] = {}

    for entry in entries:
        if entry.actual_division is None:
            continue

        division = projection.reverse_display_division(entry.actual_division)

        weight_class = entry.actual_weight_class
        if weight_class is None:
            raise ValueError("Actual weight must be set", entry)

        expected_weights = bracket_util.weights_for_division(division)
        if weight_class not in expected_weights:
            raise ValueError("Invalid weight class", division, weight_class)

        all_usaw_numbers.add(entry.usaw_number)
        key = division, weight_class
        weight_classes.setdefault(key, []).append(entry.usaw_number)

    return all_usaw_numbers, weight_classes


def _map_by_usaw(
    matches: list[bracket_util.MatchV4], all_usaw_numbers: str[str]
) -> dict[str, list[bracket_util.MatchV4]]:
    by_usaw: dict[str, list[bracket_util.MatchV4]] = {}

    for match_ in matches:
        winner_usaw_number = match_.winner_usaw_number
        if winner_usaw_number in all_usaw_numbers:
            by_athlete = by_usaw.setdefault(winner_usaw_number, [])
            by_athlete.append(match_)

        loser_usaw_number = match_.loser_usaw_number
        if loser_usaw_number in all_usaw_numbers:
            by_athlete = by_usaw.setdefault(loser_usaw_number, [])
            by_athlete.append(match_)

    return by_usaw


def _make_roster_reverse(
    rosters: list[club_util.ClubInfo], all_usaw_numbers: str[str]
) -> dict[str, tuple[str, club_util.Athlete]]:
    by_usaw: dict[str, tuple[str, club_util.Athlete]] = {}
    for roster in rosters:
        team = roster.club_name
        for athlete in roster.athletes:
            usaw_number = athlete.usaw_number
            if usaw_number not in all_usaw_numbers:
                continue

            if usaw_number in by_usaw:
                raise KeyError("Unexpected duplicate", usaw_number)

            by_usaw[usaw_number] = team, athlete

    return by_usaw


class _WeightAthlete(_ForbidExtra):
    usaw_number: str
    name: str
    ikwf_age: int
    team: str
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
            wins=wins,
            losses=losses,
            matches=matches,
            state_2025_note=state_2025_note,
        )
    )


def _weight_class_sort_func(key: tuple[bracket_util.Division, int]) -> tuple[int, int]:
    division, weight = key
    return bracket_util.sortable_division(division), weight


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
        ]
    )
    athletes = _sort_by_record(weight_class.athletes)
    for athlete in athletes:
        winning_percentage = athlete.wins / (athlete.wins + athlete.losses)

        row = [
            athlete.name,
            str(athlete.wins),
            str(athlete.losses),
            str(athlete.ikwf_age),
            athlete.usaw_number,
            athlete.team,
            athlete.state_2025_note,
            f"{winning_percentage:.3f}",
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


def main() -> None:
    entries_filename, seeding_filename = _get_filenames()

    entries = _load_entries(entries_filename)
    matches_v4 = projection.load_matches_v4()
    rosters = club_util.load_rosters()
    state_qualifiers = club_util.load_state_qualifiers()

    all_usaw_numbers, weight_classes = _preprocess_entries(entries)

    athlete_lookup = _make_roster_reverse(rosters, all_usaw_numbers)

    relevant_matches = [
        match_
        for match_ in matches_v4
        if (
            match_.winner_usaw_number in all_usaw_numbers
            or match_.loser_usaw_number in all_usaw_numbers
        )
    ]
    match_lookup = _map_by_usaw(relevant_matches, all_usaw_numbers)

    csv_weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass] = {}
    for key, weight_class_usaw in weight_classes.items():
        for usaw_number in weight_class_usaw:
            pair = athlete_lookup.get(usaw_number)
            if pair is None:
                raise ValueError("Unexpected missing athlete", usaw_number)

            team, athlete = pair
            matches = match_lookup.get(usaw_number, [])

            state_2025_note = ""
            state_qualifier = state_qualifiers.get(team, {}).get(athlete.name)
            if state_qualifier is not None:
                state_2025_note = state_qualifier.result

            _add_wrestler(
                team, key, csv_weight_classes, athlete, matches, state_2025_note
            )

    keys = sorted(csv_weight_classes.keys(), key=_weight_class_sort_func)
    sheets: dict[str, str] = {}
    for key in keys:
        key_display = projection.display_weight_class(key)
        csv_weight_class = csv_weight_classes[key]
        if key_display in sheets:
            raise TypeError("Key appears more than once", key_display)
        sheets[key_display] = _make_csv(csv_weight_class)

    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)

    for sheet_name, csv_text in sheets.items():
        if len(sheet_name) > 31:
            raise RuntimeError("Sheet name too big for Excel", sheet_name)

        worksheet = workbook.create_sheet(title=sheet_name)
        reader = csv.reader(io.StringIO(csv_text))
        for row in reader:
            worksheet.append(row)

    workbook.save(seeding_filename)


if __name__ == "__main__":
    main()
