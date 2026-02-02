import csv
import datetime
import io
import pathlib

import pandas as pd
import pydantic

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


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


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


def _get_projected_weight(
    weigh_ins: list[float], decay: float = 0.85, mad_k: float = 2.5
) -> float | None:
    weights = list(weigh_ins)
    if not weights:
        return None

    # --- Robust outlier filtering (MAD: Median Absolute Deviation) ---
    median = sorted(weights)[len(weights) // 2]
    abs_devs = [abs(weight - median) for weight in weights]
    mad = sorted(abs_devs)[len(abs_devs) // 2]

    if mad > 0:
        filtered = [weight for weight in weights if abs(weight - median) <= mad_k * mad]
    else:
        filtered = weights  # all same value

    # --- Recency weighting ---
    n = len(filtered)
    recency_weights = [decay ** (n - i - 1) for i in range(n)]

    weighted_sum = sum(
        weight * recent
        for weight, recent in zip(filtered, recency_weights, strict=True)
    )
    weight_total = sum(recency_weights)

    return weighted_sum / weight_total


def _get_athlete_weigh_ins(
    usaw_number: str, matches: list[bracket_util.MatchV4]
) -> list[float]:
    weigh_ins: dict[str, tuple[datetime.date, float]] = {}
    for match_ in matches:
        if match_.winner_usaw_number == usaw_number:
            weight = match_.winner_weight
        elif match_.loser_usaw_number == usaw_number:
            weight = match_.loser_weight
        else:
            raise RuntimeError("Match does not belong", usaw_number, match_)

        if weight is None:
            continue

        event_name = match_.event_name
        if event_name in weigh_ins:
            if weigh_ins[event_name] != (match_.event_date, weight):
                raise RuntimeError(
                    "Mismatched weigh in", event_name, usaw_number, weight
                )
            pass
        else:
            weigh_ins[event_name] = match_.event_date, weight

    by_date = sorted(weigh_ins.values())
    return [weight for _, weight in by_date]


def _slot_weight_class(
    projected: float,
    weight_classes: tuple[int, ...],
    buffer: float = 0.5,
) -> int | None:
    # NOTE: This assumes `weight_classes` is sorted from lightest to heaviest.
    for weight_class in weight_classes:
        if projected <= weight_class - buffer:
            return weight_class

    # NOTE: Too heavy
    return None


def _get_athlete_division(
    ikwf_age: int, matches: list[bracket_util.MatchV4]
) -> bracket_util.Division:
    all_divisions = set(
        match_.division for match_ in matches if match_.division is not None
    )
    is_girl = any(division.startswith("girls_") for division in all_divisions)

    if ikwf_age <= 8:
        return "girls_bantam" if is_girl else "bantam"

    if ikwf_age <= 10:
        return "girls_intermediate" if is_girl else "intermediate"

    if ikwf_age <= 12:
        return "girls_novice" if is_girl else "novice"

    if ikwf_age <= 14:
        return "girls_senior" if is_girl else "senior"

    raise ValueError("Unsupported age", ikwf_age)


def _determine_weight_class(
    usaw_number: str, ikwf_age: int, matches: list[bracket_util.MatchV4]
) -> tuple[bracket_util.Division, int] | None:
    if ikwf_age <= 6 or ikwf_age > 14:
        return None

    weigh_ins = _get_athlete_weigh_ins(usaw_number, matches)
    projected_weight = _get_projected_weight(weigh_ins)
    if projected_weight is None:
        return None

    division = _get_athlete_division(ikwf_age, matches)
    weight_classes = bracket_util.weights_for_division(division)
    weight_class = _slot_weight_class(projected_weight, weight_classes)
    if weight_class is None:
        # TODO: For younger kids, consider bumping them up
        return None

    return division, weight_class


class _WeightAthlete(_ForbidExtra):
    usaw_number: str
    name: str
    ikwf_age: int
    team: str
    wins: pydantic.NonNegativeInt
    losses: pydantic.NonNegativeInt
    matches: list[bracket_util.MatchV4]


class _WeightClass(_ForbidExtra):
    athletes: list[_WeightAthlete]
    head_to_heads: list[bracket_util.MatchV4]


def _add_wrestler(
    team: str,
    key: tuple[bracket_util.Division, int],
    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass],
    athlete: club_util.Athlete,
    matches: list[bracket_util.MatchV4],
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
        ["Name", "Wins", "Losses", "Team", "Winning percentage", "Adjusted score"]
    )
    athletes = _sort_by_record(weight_class.athletes)
    for athlete in athletes:
        winning_percentage = 0.0
        adjusted_score = _sort_helper(athlete)

        row = [
            athlete.name,
            str(athlete.wins),
            str(athlete.losses),
            athlete.team,
            f"{winning_percentage:.3f}",
            f"{adjusted_score:.3f}",
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


def _sortable_division(division: bracket_util.Division) -> int:
    if division == "bantam":
        return 1

    if division == "intermediate":
        return 2

    if division == "novice":
        return 3

    if division == "senior":
        return 4

    if division == "girls_bantam":
        return 5

    if division == "girls_intermediate":
        return 6

    if division == "girls_novice":
        return 7

    if division == "girls_senior":
        return 8

    raise RuntimeError("Unsupported division", division)


def _weight_class_sort_func(key: tuple[bracket_util.Division, int]) -> tuple[int, int]:
    division, weight = key
    return _sortable_division(division), weight


def _display_division(division: bracket_util.Division) -> int:
    if division == "bantam":
        return 1

    if division == "intermediate":
        return 2

    if division == "novice":
        return 3

    if division == "senior":
        return 4

    if division == "girls_bantam":
        return 5

    if division == "girls_intermediate":
        return 6

    if division == "girls_novice":
        return 7

    if division == "girls_senior":
        return 8

    raise RuntimeError("Unsupported division", division)


def _display_weight_class(key: tuple[bracket_util.Division, int]) -> str:
    division, weight = key
    division_str = _display_division(division)
    return f"{division_str} {weight}"


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

    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass] = {}
    for team, by_usaw in team_mapped.items():
        (athletes,) = [
            roster.athletes for roster in teams_in_sectional if roster.club_name == team
        ]
        for usaw_number, matches in by_usaw.items():
            (athlete,) = [
                athlete for athlete in athletes if athlete.usaw_number == usaw_number
            ]
            key = _determine_weight_class(usaw_number, athlete.ikwf_age, matches)
            if key is None:
                continue

            _add_wrestler(team, key, weight_classes, athlete, matches)

    keys = sorted(weight_classes.keys(), key=_weight_class_sort_func)
    sheets: dict[str, str] = {}
    for key in keys:
        key_display = _display_weight_class(key)
        weight_class = weight_classes[key]
        if key_display in sheets:
            raise TypeError("Key appears more than once", key_display)
        sheets[key_display] = _make_csv(weight_class)

    stem = bracket_util.to_kebab_case(sectional)
    xslx_filename = _ROOT / "_parsed-data" / f"{stem}.xlsx"

    with pd.ExcelWriter(xslx_filename, engine="openpyxl") as writer:
        for sheet_name, csv_text in sheets.items():
            if len(sheet_name) > 31:
                raise RuntimeError("Sheet name too big for Excel", sheet_name)

            df = pd.read_csv(io.StringIO(csv_text))
            df.to_excel(writer, sheet_name=sheet_name, index=False)


if __name__ == "__main__":
    main()
