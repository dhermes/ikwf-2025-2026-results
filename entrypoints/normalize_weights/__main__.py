import pathlib

import bracket_util
import trackwrestling

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def _parse_trackwrestling(
    raw_data_dir: pathlib.Path,
) -> list[bracket_util.AthleteWeight]:
    all_weights: list[bracket_util.AthleteWeight] = []

    for date_str, name in trackwrestling.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            all_weights.extend(trackwrestling.parse_athlete_weights(html))

    return all_weights


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"

    all_weights: list[bracket_util.AthleteWeight] = []
    all_weights.extend(_parse_trackwrestling(raw_data_dir))
    # TODO: all_weights.extend(_parse_trackwrestling_duals(raw_data_dir))
    # TODO: all_weights.extend(_parse_usabracketing(raw_data_dir))
    # TODO: all_weights.extend(_parse_usabracketing_duals(raw_data_dir))

    print(len(all_weights))


if __name__ == "__main__":
    main()
