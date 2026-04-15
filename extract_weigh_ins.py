import csv
import pathlib
import statistics
from typing import Literal

import numpy as np
import pydantic

import bracket_util
import projection

_HERE = pathlib.Path(__file__).resolve().parent
_Key = tuple[str, str, str, int]

_Gender = Literal["M", "F"]
_DESIRED_COUNTS = {
    "bantam": 13,
    "intermediate": 13,
    "novice": 15,
    "senior": 17,
    "girls_bantam": 9,
    "girls_intermediate": 11,
    "girls_novice": 13,
    "girls_senior": 16,
}
_SORTED_DIVISIONS = [
    "bantam",
    "intermediate",
    "novice",
    "senior",
    "girls_bantam",
    "girls_intermediate",
    "girls_novice",
    "girls_senior",
]


class _Mapped(pydantic.RootModel[dict[str, _Gender]]):
    pass


def _load_usaw_mapped() -> dict[str, _Gender]:
    path = _HERE / "retrospective.json"
    with open(path, "rb") as file_obj:
        content = file_obj.read()

    from_regionals = _Mapped.model_validate_json(content)
    return from_regionals.root


def _determine_gender(
    usaw_number: str | None,
    division: bracket_util.Division | None,
    usaw_mapped: dict[str, _Gender],
) -> _Gender | None:
    if usaw_number is None:
        return None

    if usaw_number in usaw_mapped:
        return usaw_mapped[usaw_number]

    if division is None:
        return None

    if division.startswith("girls_"):
        return "F"

    return None


def _merge_gender(gender1: _Gender | None, gender2: _Gender | None) -> _Gender | None:
    if gender1 is None:
        return gender2
    if gender2 is None:
        return gender1

    if gender1 != gender2:
        raise NotImplementedError
    return gender1


def _merge_key(
    weigh_ins: dict[_Key, tuple[float, _Gender | None]],
    key: _Key,
    value: tuple[float, _Gender | None],
) -> None:
    if key not in weigh_ins:
        weigh_ins[key] = value
        return

    existing = weigh_ins[key]
    if existing == value:
        return

    existing_weight, existing_gender = existing
    new_weight, new_gender = value
    if existing_weight != new_weight:
        raise NotImplementedError

    gender = _merge_gender(existing_gender, new_gender)
    weigh_ins[key] = existing_weight, gender


def _determine_division(
    ikwf_age: int, gender: _Gender | None
) -> bracket_util.Division | None:
    if gender is None:
        return None
    if ikwf_age in (4, 5, 6):
        return

    if ikwf_age in (7, 8):
        return "bantam" if gender == "M" else "girls_bantam"
    if ikwf_age in (9, 10):
        return "intermediate" if gender == "M" else "girls_intermediate"
    if ikwf_age in (11, 12):
        return "novice" if gender == "M" else "girls_novice"
    if ikwf_age in (13, 14):
        return "senior" if gender == "M" else "girls_senior"

    raise NotImplementedError(ikwf_age, gender)


def _add_row_to_aggregate(
    by_division: dict[bracket_util.Division, dict[str, list[float]]],
    usaw_number: str,
    weight: float,
    ikwf_age: int,
    gender: _Gender,
) -> None:
    division = _determine_division(ikwf_age, gender)
    if division is None:
        return

    by_division.setdefault(division, {})
    by_division[division].setdefault(usaw_number, [])
    by_division[division][usaw_number].append(weight)


def _athlete_weight_guesstimate(weigh_ins: list[float]) -> float:
    return statistics.median(weigh_ins)


def _median_from_aggregate(
    by_division: dict[bracket_util.Division, dict[str, list[float]]],
) -> dict[bracket_util.Division, list[float]]:
    result: dict[bracket_util.Division, list[float]] = {}
    for division, athletes in by_division.items():
        within_division: list[float] = []
        result[division] = within_division
        for weigh_ins in athletes.values():
            median_weight = _athlete_weight_guesstimate(weigh_ins)
            within_division.append(median_weight)

    return result


def _create_weight_classes(
    weights: list[float],
    num_classes: int,
    drop_top_pct: float = 0.02,  # drop top 2% as outliers
) -> list[tuple[int, int]]:
    if not weights:
        raise NotImplementedError

    w = np.array(sorted(weights))

    # Optionally drop extreme heavy outliers
    if drop_top_pct > 0:
        cutoff_index = int(len(w) * (1 - drop_top_pct))
        w = w[:cutoff_index]

    # Compute quantile breakpoints
    quantiles = np.linspace(0, 1, num_classes + 1)
    edges = np.quantile(w, quantiles)

    # Build class ranges
    classes: list[tuple[int, int]] = []
    for i in range(num_classes):
        low_exact = edges[i]
        high_exact = edges[i + 1]

        # Round for cleaner class boundaries (optional)
        low = int(round(low_exact))
        high = int(round(high_exact))

        if i == 0:
            low = 0

        count = int(((w > low) & (w <= high)).sum())

        classes.append((high, count))

    highest = classes[-1][0]
    excluded_count = int(((w > highest)).sum())
    if excluded_count > 0:
        classes.append((999, excluded_count))

    return classes


def main() -> None:
    usaw_mapped = _load_usaw_mapped()

    matches_v4 = projection.load_matches_v4()
    weigh_ins: dict[_Key, tuple[float, _Gender | None]] = {}
    for match_ in matches_v4:
        event_date = match_.event_date
        event_name = match_.event_name
        winner_usaw_number = match_.winner_usaw_number
        winner_weight = match_.winner_weight
        winner_gender = _determine_gender(
            match_.winner_usaw_number, match_.division, usaw_mapped
        )
        loser_usaw_number = match_.loser_usaw_number
        loser_weight = match_.loser_weight
        loser_gender = _determine_gender(
            match_.loser_usaw_number, match_.division, usaw_mapped
        )

        if winner_usaw_number is not None and winner_weight is not None:
            if match_.winner_ikwf_age is None:
                raise NotImplementedError
            key = (
                event_name,
                str(event_date),
                winner_usaw_number,
                match_.winner_ikwf_age,
            )
            value = winner_weight, winner_gender
            _merge_key(weigh_ins, key, value)

        if loser_usaw_number is not None and loser_weight is not None:
            if match_.loser_ikwf_age is None:
                raise NotImplementedError
            key = (
                event_name,
                str(event_date),
                loser_usaw_number,
                match_.loser_ikwf_age,
            )
            value = loser_weight, loser_gender
            _merge_key(weigh_ins, key, value)

    total_count = 0
    missing_count = 0

    by_division: dict[bracket_util.Division, dict[str, list[float]]] = {}
    with open(_HERE / "extracted-weigh-ins.csv", "w") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(
            ("Event name", "Event date", "USAW number", "IKWF age", "Weight", "Gender")
        )
        for key, value in weigh_ins.items():
            event_name, event_date, usaw_number, ikwf_age = key
            weight, gender = value
            _add_row_to_aggregate(by_division, usaw_number, weight, ikwf_age, gender)

            total_count += 1
            if gender is None:
                missing_count += 1

            row = (
                event_name,
                event_date,
                usaw_number,
                str(ikwf_age),
                str(weight),
                gender,
            )
            writer.writerow(row)

    # 21109 out of 74258 (28.4%) weigh ins still missing gender
    missing_percent = 100 * missing_count / total_count
    print(f"Missing: {missing_count} / {total_count} ({missing_percent:.1f}%)")

    one_weight = _median_from_aggregate(by_division)
    for division in _SORTED_DIVISIONS:
        weights = one_weight[division]
        desired_count = _DESIRED_COUNTS[division]
        weight_classes = _create_weight_classes(weights, desired_count)
        print(f"{division}:")
        for weight, athlete_count in weight_classes:
            if weight == 999:
                print(f"- {athlete_count} athletes too heavy")
            else:
                print(f"- {weight} lbs ({athlete_count} athletes)")
        print("")


if __name__ == "__main__":
    main()
