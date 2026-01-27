import pathlib

import bracket_util
import usabracketing

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def main() -> None:
    login_info = usabracketing.get_login_info()

    raw_data_dir = _ROOT / "_raw-data"
    for date_str, name in usabracketing.DUAL_EVENTS:
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
        weights_html = usabracketing.fetch_dual_weights(event, login_info)
        if not weights_html:
            raise RuntimeError("Event has no weights", name)

        to_serialize = bracket_util.FetchedEvent(
            name=event.name,
            source="usabracketing_dual",
            start_date=event.start_date,
            end_date=event.end_date,
            match_html=weights_html,
        )
        as_json = to_serialize.model_dump_json(indent=2)
        with open(path, "w") as file_obj:
            file_obj.write(as_json)
            file_obj.write("\n")


if __name__ == "__main__":
    main()
