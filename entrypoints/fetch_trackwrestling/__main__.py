import json
import pathlib
import re

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
2025-12-07 | Lil` Coalers Clash
2025-12-07 | Lincoln Railer Rumble 2025
2025-12-07 | Peoria Razorback Season Opener
2025-12-07 | Tiger Takedown
2025-12-13 | 2025 O`Fallon Beginners/Girls Open
2025-12-13 | Mattoon Beginners Tournament
2025-12-14 | 2025 Beat the Streets Youth Brawl
2025-12-14 | 2025 Hub City Hammer Duals
2025-12-14 | 2025 Orland Park Pioneer KickOff Classic
2025-12-14 | ACES Rumble
2025-12-14 | Countdown to Christmas DGWC
2025-12-14 | December 2025 Lil Reapers Wrestling Classic
2025-12-14 | John Nagy Throwdown 2025
2025-12-14 | Rumble on the Red
2025-12-14 | CICC Classic
2025-12-14 | Wilbur Borrero Classic
2025-12-21 | 2025 Mat Rat Invitational
2025-12-21 | 2025 Yeti Bash/Morris Kids WC
2025-12-21 | 309 Winter Classic
2025-12-21 | Bulldog Brawl
2025-12-21 | Clinton Challenge
2025-12-21 | Cumberland Kids Open 2025
2025-12-21 | Darby Pool Wrestling Tournament
2025-12-21 | Highland Howl Jarron Haberer memorial
2025-12-21 | Joe Tholl Sr. ELITE/OPEN 2025
2025-12-21 | 2025 Rocket Blast
2025-12-21 | Jr. Porter Invite
2025-12-21 | Spartan Beginner Tournament
2025-12-21 | Stillman Valley Holiday Tournament
2025-12-27 | Betty Martinez Memorial
2025-12-27 | D/C Bolts New Years Bash
2025-12-27 | Roughnecks Christmas Classic
2025-12-28 | Brawlers Brawl 2025
2025-12-28 | Reindeer Rumble
2025-12-28 | Dave Mattio Classic
2025-12-28 | Crawford County Open
2025-12-28 | Sandwich WinterWonderSlam
2025-12-28 | Junior Midlands
2025-12-28 | Granite City Kids Holiday Classic
2025-12-30 | Rockford Bad Boys & Girls Open
2025-12-31 | Cadet Classic
2026-01-03 | Boneyard Bash
2026-01-03 | Hillsboro Jr. Toppers Tournament
2026-01-03 | Double D Demolition
2026-01-04 | Brady Girls Open
2026-01-04 | Oak Lawn Acorn Rookie Rumble
2026-01-04 | Midwest Classic
2026-01-04 | Monticello Youth Open
2026-01-04 | Little Giant Holiday Hammer
2026-01-04 | Crushing Christmas Classic
2026-01-04 | Bob Jahn Memorial
2026-01-04 | Mattoon YWC Bonic Battle for the Belt
2026-01-04 | Peyton Smith Open hosted by BWC
2026-01-04 | IKWF Southern Dual Meet Divisional
2026-01-10 | Didi Duals
2026-01-10 | Fisher Jamboree
2026-01-10 | Hawk Wrestling Club Invitational
2026-01-10 | Stillman Valley Beginners Tournament
2026-01-11 | Batavia Classic
2026-01-11 | Carbondale Dog Fight & Alli Ragan Girls Open
2026-01-11 | Coach Jim Craig Memorial
2026-01-11 | Geneva Junior Vikings Youth Open
2026-01-11 | Jacksonville Area Wrestling Battle in the Bowl
2026-01-11 | Little Devils Gauntlet
2026-01-11 | Mt Zion Kids Club Open
2026-01-11 | Pontiac Kids Open
2026-01-11 | Wolfpack Open"""


def _to_kebab_case(name: str) -> str:
    # Lowercase
    name = name.lower()

    # Remove special characters
    name = re.sub(r"[`~!@#$%^&*()=+\[\]{}\\|;:'\",<>/?]", "", name)

    # Replace spaces or underscores with hyphen
    name = re.sub(r"[ _]+", "-", name)

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    # Strip leading/trailing hyphens
    name = name.strip("-")

    return name


def main() -> None:
    raw_data_dir = _ROOT / "_raw-data"
    for row in _TOURNAMENTS.split("\n"):
        date_str, name = row.split(" | ")
        parent_dir = raw_data_dir / date_str
        parent_dir.mkdir(parents=True, exist_ok=True)

        stem = _to_kebab_case(name)
        filename = f"{stem}.json"
        path = parent_dir / filename
        if path.exists():
            print(f"Skipping: {name} ...")
            continue

        tournament = trackwrestling.Tournament(
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
