import pathlib

import bracket_util
import trackwrestling

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def _fetch_event_rounds(
    path: pathlib.Path, event: bracket_util.Event
) -> bracket_util.FetchedEvent:
    if path.exists():
        with open(path, "rb") as file_obj:
            as_json = file_obj.read()

        return bracket_util.FetchedEvent.model_validate_json(as_json)

    print(f"Fetching rounds for: {event.name} ...")
    rounds_html = trackwrestling.fetch_tournament_rounds(event)

    if not rounds_html:
        raise RuntimeError("Tournament has no rounds", event.name)

    fetched_event = bracket_util.FetchedEvent(
        name=event.name,
        source="trackwrestling",
        start_date=event.start_date,
        end_date=event.end_date,
        match_html=rounds_html,
        weights_html={},
    )
    return fetched_event


def _fetch_event_athlete_weights(
    fetched_event: bracket_util.FetchedEvent, event: bracket_util.Event
) -> bracket_util.FetchedEvent | None:
    if fetched_event.weights_html:
        print(f"Skipping: {event.name} ...")
        return None

    print(f"Fetching athlete weights for: {event.name} ...")

    weights_html = trackwrestling.fetch_athlete_weights(event)

    if not weights_html:
        raise RuntimeError("Tournament has no athlete weights", event.name)

    fetched_event.weights_html = weights_html
    return fetched_event


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"
    for date_str, name in trackwrestling.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        parent_dir.mkdir(parents=True, exist_ok=True)

        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename

        event = bracket_util.Event(name=name, start_date=None, end_date=date_str)
        fetched_event = _fetch_event_rounds(path, event)
        fetched_event = _fetch_event_athlete_weights(fetched_event, event)

        if fetched_event is None:
            continue

        as_json = fetched_event.model_dump_json(indent=2)
        with open(path, "w") as file_obj:
            file_obj.write(as_json)
            file_obj.write("\n")


if __name__ == "__main__":
    main()
