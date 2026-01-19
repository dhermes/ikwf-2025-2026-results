import json
import pathlib

import bracket_util
import usabracketing

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


def main() -> None:
    login_info = usabracketing.get_login_info()

    raw_data_dir = _ROOT / "_raw-data"
    for date_str, name in usabracketing.TOURNAMENT_EVENTS:
        parent_dir = raw_data_dir / date_str
        parent_dir.mkdir(parents=True, exist_ok=True)

        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename
        if path.exists():
            print(f"Skipping: {name} ...")
            continue

        tournament = bracket_util.Tournament(
            name=name, start_date=None, end_date=date_str
        )

        print(f"Fetching: {name} ...")
        captured_html = usabracketing.fetch_tournament_rounds(tournament, login_info)
        if not captured_html:
            raise RuntimeError("Tournament has no rounds", name)

        with open(path, "w") as file_obj:
            json.dump(captured_html, file_obj, sort_keys=True, indent=2)
            file_obj.write("\n")


if __name__ == "__main__":
    main()
