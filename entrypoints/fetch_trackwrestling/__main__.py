import pathlib

import bracket_util
import trackwrestling

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"
    for date_str, name in trackwrestling.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        parent_dir.mkdir(parents=True, exist_ok=True)

        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename
        if path.exists():
            print(f"Skipping: {name} ...")
            continue

        event = bracket_util.Event(name=name, start_date=None, end_date=date_str)

        print(f"Fetching: {name} ...")
        rounds_html = trackwrestling.fetch_tournament_rounds(event)

        if not rounds_html:
            raise RuntimeError("Tournament has no rounds", name)

        to_serialize = bracket_util.FetchedEvent(
            name=event.name,
            source="trackwrestling",
            start_date=event.start_date,
            end_date=event.end_date,
            match_html=rounds_html,
        )
        as_json = to_serialize.model_dump_json(indent=2)
        with open(path, "w") as file_obj:
            file_obj.write(as_json)
            file_obj.write("\n")


if __name__ == "__main__":
    main()
