import json
import pathlib

import bracket_util
import usabracketing

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

# TODO: 2026-01-04 | IKWF Southern Dual Meet Divisional
# TODO: 2026-01-18 | Jon Davis Kids Open
_TOURNAMENTS = """\
2025-12-07 | 42nd Annual Bulls Wrestling Tournament
2025-12-14 | CICC Classic
2025-12-14 | Wilbur Borrero Classic
2025-12-20 | 2025 Edwardsville Open
2025-12-21 | 2025 Rocket Blast
2025-12-21 | Jr. Porter Invite
2025-12-21 | Spartan Beginner Tournament
2025-12-21 | Stillman Valley Holiday Tournament
2025-12-28 | Granite City Kids Holiday Classic
2025-12-30 | Rockford Bad Boys & Girls Open
2026-01-10 | Stillman Valley Beginners Tournament
2026-01-11 | Chauncey Carrick Good Guys Tournament
2026-01-11 | Morton Youth Wrestling 2026
2026-01-11 | Spartan 300"""


def main() -> None:
    login_info = usabracketing.get_login_info()

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
