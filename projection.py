import csv
import datetime
import pathlib

import pydantic

import bracket_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE
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


def load_matches_v4() -> list[bracket_util.MatchV4]:
    input_file = _ROOT / "_parsed-data" / "all-matches-04.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        for key in _NULLABLE_KEYS:
            if row[key] == "":
                row[key] = None

    matches_root = bracket_util.MatchesV4.model_validate(rows)
    return matches_root.root


class _Regionals(pydantic.RootModel[dict[str, list[str]]]):
    pass


def get_regional_assignments() -> dict[str, list[str]]:
    with open(_ROOT / "_parsed-data" / "regionals.json", "rb") as file_obj:
        as_json = file_obj.read()

    regionals = _Regionals.model_validate_json(as_json)
    return regionals.root


def map_by_team(
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
) -> tuple[list[float], datetime.date, float]:
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
    weigh_in_amounts = [weight for _, weight in by_date]
    if by_date:
        most_recent_weigh_in, most_recent_weight = by_date[-1]
    else:
        most_recent_weigh_in = datetime.date(1970, 1, 1)
        most_recent_weight = 0.0
    return weigh_in_amounts, most_recent_weigh_in, most_recent_weight


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


def determine_weight_class(
    usaw_number: str, ikwf_age: int, matches: list[bracket_util.MatchV4]
) -> tuple[tuple[bracket_util.Division, int], datetime.date, float, float] | None:
    if ikwf_age <= 6 or ikwf_age > 14:
        return None

    weigh_ins, most_recent_weigh_in, most_recent_weight = _get_athlete_weigh_ins(
        usaw_number, matches
    )
    projected_weight = _get_projected_weight(weigh_ins)
    if projected_weight is None:
        return None

    division = _get_athlete_division(ikwf_age, matches)
    weight_classes = bracket_util.weights_for_division(division)
    weight_class = _slot_weight_class(projected_weight, weight_classes)
    if weight_class is None:
        # TODO: For younger kids, consider bumping them up
        return None

    return (
        (division, weight_class),
        most_recent_weigh_in,
        most_recent_weight,
        projected_weight,
    )


def display_division(division: bracket_util.Division) -> str:
    if division == "bantam":
        return "Bantam"

    if division == "intermediate":
        return "Intermediate"

    if division == "novice":
        return "Novice"

    if division == "senior":
        return "Senior"

    if division == "girls_bantam":
        return "Girls Bantam"

    if division == "girls_intermediate":
        return "Girls Intermediate"

    if division == "girls_novice":
        return "Girls Novice"

    if division == "girls_senior":
        return "Girls Senior"

    raise RuntimeError("Unsupported division", division)


def reverse_display_division(division_str: str) -> bracket_util.Division:
    if division_str == "Bantam":
        return "bantam"

    if division_str == "Intermediate":
        return "intermediate"

    if division_str == "Novice":
        return "novice"

    if division_str == "Senior":
        return "senior"

    if division_str == "Girls Bantam":
        return "girls_bantam"

    if division_str == "Girls Intermediate":
        return "girls_intermediate"

    if division_str == "Girls Novice":
        return "girls_novice"

    if division_str == "Girls Senior":
        return "girls_senior"

    raise RuntimeError("Unsupported division", division_str)


def display_weight_class(key: tuple[bracket_util.Division, int]) -> str:
    division, weight = key
    division_str = display_division(division)
    return f"{division_str} {weight}"
