import json
import pathlib

import bracket_util
import trackwrestling

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

_TOURNAMENTS = """\
2025-12-14 | 2025 Hub City Hammer Duals
2026-01-10 | The Didi Duals 2026"""


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"
    for row in _TOURNAMENTS.split("\n"):
        date_str, name = row.split(" | ")
        parent_dir = raw_data_dir / date_str
        parent_dir.mkdir(parents=True, exist_ok=True)

        stem = bracket_util.to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename
        if path.exists():
            print(f"Skipping: {name} ...")
            continue

        tournament = trackwrestling.Tournament(
            name=name, start_date=None, end_date=date_str
        )

        print(f"Fetching: {name} ...")
        captured_html = trackwrestling.fetch_dual_weights(tournament)
        if not captured_html:
            raise RuntimeError("Tournament has no weights", name)

        with open(path, "w") as file_obj:
            json.dump(captured_html, file_obj, sort_keys=True, indent=2)
            file_obj.write("\n")


if __name__ == "__main__":
    main()
