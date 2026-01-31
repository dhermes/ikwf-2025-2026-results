import pathlib

import bracket_util
import trackwrestling
import usabracketing

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


_MappedAthletes = dict[bracket_util.AthleteWeightKey, bracket_util.AthleteWeight]


def _merge_into_results(
    page: _MappedAthletes, results: _MappedAthletes
) -> _MappedAthletes:
    for key, value in page.items():
        if key in results:
            if results[key] != value:
                raise ValueError(
                    "Unexpected non-matching rows", key, value, results[key]
                )
        else:
            results[key] = value

    return results


def _parse_trackwrestling(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in trackwrestling.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = trackwrestling.parse_athlete_weights(html, "trackwrestling")
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def _parse_trackwrestling_duals(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in trackwrestling.DUAL_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = trackwrestling.parse_athlete_weights(
                html, "trackwrestling_dual"
            )
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def _parse_usabracketing(
    raw_data_dir: pathlib.Path,
) -> dict[str, _MappedAthletes]:
    by_event: dict[str, _MappedAthletes] = {}

    for date_str, name in usabracketing.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        with open(path) as file_obj:
            as_json = file_obj.read()

        fetched_event = bracket_util.FetchedEvent.model_validate_json(as_json)
        athlete_weights_raw = fetched_event.weights_html

        event_weights: _MappedAthletes = {}

        keys = sorted(athlete_weights_raw.keys())
        for key in keys:
            html = athlete_weights_raw[key]
            page_weights = usabracketing.parse_athlete_weights(html)
            event_weights = _merge_into_results(page_weights, event_weights)

        by_event[fetched_event.name] = event_weights

    return by_event


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"

    by_event = _parse_trackwrestling(raw_data_dir)
    by_event.update(_parse_trackwrestling_duals(raw_data_dir))
    by_event.update(_parse_usabracketing(raw_data_dir))
    # TODO: by_event.update(_parse_usabracketing_duals(raw_data_dir))

    print(len(by_event))
    print(sum(len(athletes) for athletes in by_event.values()))


if __name__ == "__main__":
    main()
