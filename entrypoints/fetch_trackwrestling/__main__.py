import json
import pathlib

import bracket_util
import trackwrestling

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent

_TOURNAMENTS = """\
2025-12-06 | 2025 EWC Beginners and Girls Tournament
2025-12-06 | Tots Bash
2025-12-07 | 2025 Force Challenge 19
2025-12-07 | 2025 Mick Ruettiger Invitational
2025-12-07 | 2025 Oak Forest Green and White Tournament
2025-12-07 | 2025 Xtreme Challenge
2025-12-07 | Capture the Eagle
2025-12-07 | Elias George Memorial 2025
2025-12-07 | Fox Lake Beginners Tournament
2025-12-07 | Lawrence County Knights Terry Hoke Open
2025-12-07 | Lil` Coalers Clash
2025-12-07 | Lincoln Railer Rumble 2025
2025-12-07 | Peoria Razorback Season Opener
2025-12-07 | Tiger Takedown
2025-12-13 | 2025 O`Fallon Beginners/Girls Open
2025-12-13 | Mattoon Beginners Tournament
2025-12-13 | Roxana Rumble
2025-12-14 | 2025 Beat the Streets Youth Brawl
2025-12-14 | 2025 Orland Park Pioneer KickOff Classic
2025-12-14 | ACES Rumble
2025-12-14 | Countdown to Christmas DGWC
2025-12-14 | December 2025 Lil Reapers Wrestling Classic
2025-12-14 | John Nagy Throwdown 2025
2025-12-14 | Rumble on the Red
2025-12-20 | 2025 Edwardsville Open
2025-12-21 | 2025 Mat Rat Invitational
2025-12-21 | 2025 Yeti Bash/Morris Kids WC
2025-12-21 | 309 Winter Classic
2025-12-21 | Bulldog Brawl
2025-12-21 | Clinton Challenge
2025-12-21 | Cumberland Kids Open 2025
2025-12-21 | Darby Pool Wrestling Tournament
2025-12-21 | Highland Howl Jarron Haberer memorial
2025-12-21 | Joe Tholl Sr. ELITE/OPEN 2025
2025-12-27 | 2025 Betty Martinez Memorial
2025-12-27 | D/C Bolt New Years Bash
2025-12-28 | 2025 Naperville Reindeer Rumble
2025-12-28 | 2025 Dave Mattio Classic
2025-12-28 | Crawford County Open
2025-12-28 | 2025 Sandwich WinterWonderSLAM
2025-12-28 | Junior Midlands @ Northwestern University
2025-12-31 | Cadet Classic
2026-01-03 | 2026 Boneyard Bash ELITE & ROOKIE
2026-01-03 | 2026 Hillsboro Jr. Topper Tournament
2026-01-03 | Double D Demolition (SVWC Tournament)
2026-01-04 | Oak Lawn Acorn Rookie Rumble
2026-01-04 | THE Midwest Classic 2026
2026-01-04 | Monticello Youth Open 2026
2026-01-04 | The Little Giant Holiday Hammer
2026-01-04 | Crushing Christmas Classic-Coal City
2026-01-04 | 2026 Bob Jahn Memorial
2026-01-04 | Mattoon YWC - Bonic Battle for the Belt
2026-01-10 | Hawk Wrestling Club Invitational
2026-01-11 | Batavia Classic Wrestling Tournament
2026-01-11 | 2026CarbondaleDogFight&AlliRaganGirlsOpn
2026-01-11 | 2026 Coach Jim Craig Memorial-CLOSED
2026-01-11 | Geneva Vikings Youth Tournament
2026-01-11 | Devils Gauntlet Battle for the Belts
2026-01-11 | Mt Zion kids club open
2026-01-11 | Pontiac Kids Open 2026
2026-01-11 | JAWS Battle in the Bowl"""


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

        tournament = bracket_util.Tournament(
            name=name, start_date=None, end_date=date_str
        )

        print(f"Fetching: {name} ...")
        captured_html = trackwrestling.fetch_tournament_rounds(tournament)
        if not captured_html:
            raise RuntimeError("Tournament has no rounds", name)

        with open(path, "w") as file_obj:
            json.dump(captured_html, file_obj, sort_keys=True, indent=2)
            file_obj.write("\n")


if __name__ == "__main__":
    main()
