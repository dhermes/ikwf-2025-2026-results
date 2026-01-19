import csv
import json
import pathlib

import bracket_util
import trackwrestling
import usabracketing

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def _parse_trackwrestling(raw_data_dir: pathlib.Path) -> list[bracket_util.Match]:
    all_matches: list[bracket_util.Match] = []

    for date_str, name in trackwrestling.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            rounds_raw = json.load(file_obj)

        rounds = sorted(rounds_raw.keys())
        for round_ in rounds:
            html = rounds_raw[round_]
            all_matches.extend(
                trackwrestling.parse_tournament_round(html, name, date_str)
            )

    return all_matches


def _parse_trackwrestling_duals(raw_data_dir: pathlib.Path) -> list[bracket_util.Match]:
    all_matches: list[bracket_util.Match] = []

    for date_str, name in trackwrestling.DUAL_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            weights_raw = json.load(file_obj)

        all_matches.extend(trackwrestling.parse_dual_event(weights_raw, name, date_str))

    return all_matches


def _parse_usabracketing(raw_data_dir: pathlib.Path) -> list[bracket_util.Match]:
    all_matches: list[bracket_util.Match] = []

    for date_str, name in usabracketing.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            rounds_raw = json.load(file_obj)

        rounds = sorted(rounds_raw.keys())
        for round_ in rounds:
            html = rounds_raw[round_]
            all_matches.extend(
                usabracketing.parse_tournament_round(html, name, date_str)
            )

    return all_matches


def _parse_usabracketing_duals(raw_data_dir: pathlib.Path) -> list[bracket_util.Match]:
    all_matches: list[bracket_util.Match] = []

    for date_str, name in usabracketing.DUAL_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            weights_raw = json.load(file_obj)

        weights = sorted(weights_raw.keys())

    return all_matches


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"

    all_matches: list[bracket_util.Match] = []
    all_matches.extend(_parse_trackwrestling(raw_data_dir))
    all_matches.extend(_parse_trackwrestling_duals(raw_data_dir))
    all_matches.extend(_parse_usabracketing(raw_data_dir))
    all_matches.extend(_parse_usabracketing_duals(raw_data_dir))

    all_matches_file = _ROOT / "_parsed-data" / "all-matches.csv"
    with open(all_matches_file, "w") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=bracket_util.CSV_FIELD_NAMES)
        writer.writeheader()
        for match_ in all_matches:
            writer.writerow(match_.model_dump(mode="json", by_alias=True))


if __name__ == "__main__":
    main()
