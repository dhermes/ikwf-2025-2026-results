# IKWF 2025-2026 Results

> Public dataset for all 2025-2026 [IKWF][1] results

- The goal is to help in seeding for postseason tournaments
- Can also help clubs with evaluating wrestlers across seasons

The [2025-2026 All IKWF Matches][2] Google Sheet will be updated periodically to
showcase all the parsed and normalized matches.

## Tricks

- For TrackWrestling, get results **by round** and then go to "Advanced" and use
  a format with a `::` delimiter so they are easy to parse
  `[boutType] :: [wFName] :: [wLName] :: [wTeam] :: [winType] :: [lFName] :: [lLName] :: [lTeam] :: [scoreSummary]`
  - This is enabled by `uv run python -m entrypoints.fetch_trackwrestling`
- For USA Bracketing, go to "Reports" and then select "AP Bouts by Division,
  Round then Weight" and go until all rounds are extracted (**by round**)

## Season tournaments

| Raw                | Date       | Tournament                                    | Source         |
| ------------------ | ---------- | --------------------------------------------- | -------------- |
| :white_check_mark: | 2025-12-06 | 2025 EWC Beginners and Girls Tournament       | TrackWrestling |
| :white_check_mark: | 2025-12-06 | Tots Bash                                     | TrackWrestling |
| :white_check_mark: | 2025-12-07 | 2025 Force Challenge 19                       | TrackWrestling |
| :white_check_mark: | 2025-12-07 | 2025 Mick Ruettiger Invitational              | TrackWrestling |
| :white_check_mark: | 2025-12-07 | 2025 Oak Forest Green and White Tournament    | TrackWrestling |
| :white_check_mark: | 2025-12-07 | 2025 Xtreme Challenge                         | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Capture the Eagle                             | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Elias George Memorial 2025                    | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Fox Lake Beginners Tournament                 | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Lawrence County Knights Terry Hoke Open       | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Lil` Coalers Clash                            | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Lincoln Railer Rumble 2025                    | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Peoria Razorback Season Opener                | TrackWrestling |
| :white_check_mark: | 2025-12-07 | Tiger Takedown                                | TrackWrestling |
| :white_check_mark: | 2025-12-07 | 42nd Annual Bulls Wrestling Tournament        | USA Bracketing |
| :white_check_mark: | 2025-12-13 | 2025 O`Fallon Beginners/Girls Open            | TrackWrestling |
| :white_check_mark: | 2025-12-13 | Mattoon Beginners Tournament                  | TrackWrestling |
| :white_check_mark: | 2025-12-13 | Roxana Rumble                                 | TrackWrestling |
| :white_check_mark: | 2025-12-14 | 2025 Beat the Streets Youth Brawl             | TrackWrestling |
| :white_check_mark: | 2025-12-14 | 2025 Hub City Hammer Duals                    | TrackWrestling |
| :white_check_mark: | 2025-12-14 | 2025 Orland Park Pioneer KickOff Classic      | TrackWrestling |
| :white_check_mark: | 2025-12-14 | ACES Rumble                                   | TrackWrestling |
| :white_check_mark: | 2025-12-14 | Countdown to Christmas DGWC                   | TrackWrestling |
| :white_check_mark: | 2025-12-14 | December 2025 Lil Reapers Wrestling Classic   | TrackWrestling |
| :white_check_mark: | 2025-12-14 | John Nagy Throwdown 2025                      | TrackWrestling |
| :white_check_mark: | 2025-12-14 | Rumble on the Red                             | TrackWrestling |
| :white_check_mark: | 2025-12-14 | CICC Classic                                  | USA Bracketing |
| :white_check_mark: | 2025-12-14 | Wilbur Borrero Classic                        | USA Bracketing |
| :white_check_mark: | 2025-12-20 | 2025 Edwardsville Open                        | TrackWrestling |
| :white_check_mark: | 2025-12-21 | 2025 Mat Rat Invitational                     | TrackWrestling |
| :white_check_mark: | 2025-12-21 | 2025 Yeti Bash/Morris Kids WC                 | TrackWrestling |
| :white_check_mark: | 2025-12-21 | 309 Winter Classic                            | TrackWrestling |
| :white_check_mark: | 2025-12-21 | Bulldog Brawl                                 | TrackWrestling |
| :white_check_mark: | 2025-12-21 | Clinton Challenge                             | TrackWrestling |
| :white_check_mark: | 2025-12-21 | Cumberland Kids Open 2025                     | TrackWrestling |
| :white_check_mark: | 2025-12-21 | Darby Pool Wrestling Tournament               | TrackWrestling |
| :white_check_mark: | 2025-12-21 | Highland Howl Jarron Haberer memorial         | TrackWrestling |
| :white_check_mark: | 2025-12-21 | Joe Tholl Sr. ELITE/OPEN 2025                 | TrackWrestling |
| :white_check_mark: | 2025-12-21 | 2025 Rocket Blast                             | USA Bracketing |
| :white_check_mark: | 2025-12-21 | Jr. Porter Invite                             | USA Bracketing |
| :white_check_mark: | 2025-12-21 | Spartan Beginner Tournament                   | USA Bracketing |
| :white_check_mark: | 2025-12-21 | Stillman Valley Holiday Tournament            | USA Bracketing |
| :white_check_mark: | 2025-12-27 | 2025 Betty Martinez Memorial                  | TrackWrestling |
| :white_check_mark: | 2025-12-27 | D/C Bolt New Years Bash                       | TrackWrestling |
| :white_check_mark: | 2025-12-28 | 2025 Dave Mattio Classic                      | TrackWrestling |
| :white_check_mark: | 2025-12-28 | 2025 Naperville Reindeer Rumble               | TrackWrestling |
| :white_check_mark: | 2025-12-28 | 2025 Sandwich WinterWonderSLAM                | TrackWrestling |
| :white_check_mark: | 2025-12-28 | Crawford County Open                          | TrackWrestling |
| :white_check_mark: | 2025-12-28 | Junior Midlands @ Northwestern University     | TrackWrestling |
| :white_check_mark: | 2025-12-28 | Granite City Kids Holiday Classic             | USA Bracketing |
| :white_check_mark: | 2025-12-30 | Rockford Bad Boys & Girls Open                | USA Bracketing |
| :white_check_mark: | 2025-12-31 | Cadet Classic                                 | TrackWrestling |
| :white_check_mark: | 2026-01-03 | 2026 Boneyard Bash ELITE & ROOKIE             | TrackWrestling |
| :white_check_mark: | 2026-01-03 | 2026 Hillsboro Jr. Topper Tournament          | TrackWrestling |
| :white_check_mark: | 2026-01-03 | Double D Demolition (SVWC Tournament)         | TrackWrestling |
| :white_check_mark: | 2026-01-04 | 2026 Bob Jahn Memorial                        | TrackWrestling |
| :white_check_mark: | 2026-01-04 | Crushing Christmas Classic-Coal City          | TrackWrestling |
| :white_check_mark: | 2026-01-04 | Mattoon YWC - Bonic Battle for the Belt       | TrackWrestling |
| :white_check_mark: | 2026-01-04 | Monticello Youth Open 2026                    | TrackWrestling |
| :white_check_mark: | 2026-01-04 | Oak Lawn Acorn Rookie Rumble                  | TrackWrestling |
| :white_check_mark: | 2026-01-04 | The Little Giant Holiday Hammer               | TrackWrestling |
| :white_check_mark: | 2026-01-04 | THE Midwest Classic 2026                      | TrackWrestling |
| :white_check_mark: | 2026-01-04 | IKWF Southern Dual Meet Divisional            | USA Bracketing |
| :white_check_mark: | 2026-01-10 | Hawk Wrestling Club Invitational              | TrackWrestling |
| :white_check_mark: | 2026-01-10 | The Didi Duals 2026                           | TrackWrestling |
| :white_check_mark: | 2026-01-10 | Stillman Valley Beginners Tournament          | USA Bracketing |
| :white_check_mark: | 2026-01-11 | 2026 Coach Jim Craig Memorial-CLOSED          | TrackWrestling |
| :white_check_mark: | 2026-01-11 | 2026CarbondaleDogFight&AlliRaganGirlsOpn      | TrackWrestling |
| :white_check_mark: | 2026-01-11 | Batavia Classic Wrestling Tournament          | TrackWrestling |
| :white_check_mark: | 2026-01-11 | Devils Gauntlet Battle for the Belts          | TrackWrestling |
| :white_check_mark: | 2026-01-11 | Geneva Vikings Youth Tournament               | TrackWrestling |
| :white_check_mark: | 2026-01-11 | JAWS Battle in the Bowl                       | TrackWrestling |
| :white_check_mark: | 2026-01-11 | Mt Zion kids club open                        | TrackWrestling |
| :white_check_mark: | 2026-01-11 | Pontiac Kids Open 2026                        | TrackWrestling |
| :white_check_mark: | 2026-01-11 | Chauncey Carrick Good Guys Tournament         | USA Bracketing |
| :white_check_mark: | 2026-01-11 | Morton Youth Wrestling 2026                   | USA Bracketing |
| :white_check_mark: | 2026-01-11 | Spartan 300                                   | USA Bracketing |
| :white_check_mark: | 2026-01-18 | Jon Davis Kids Open                           | USA Bracketing |
| :white_check_mark: | 2026-01-24 | 2026 Girls Rule Rumble                        | TrackWrestling |
| :white_check_mark: | 2026-01-25 | 2026 Ezra Hill Jr Memorial Tournament         | TrackWrestling |
| :white_check_mark: | 2026-01-25 | 2026 Susan Collins Memorial Tournament        | TrackWrestling |
| :white_check_mark: | 2026-01-25 | Cabin Fever 2026                              | TrackWrestling |
| :white_check_mark: | 2026-01-25 | Celtic Open 2026                              | TrackWrestling |
| :white_check_mark: | 2026-01-25 | DEMOLITION BATTLE OF RAGNAROK                 | TrackWrestling |
| :white_check_mark: | 2026-01-25 | Geist Grappling Classic                       | TrackWrestling |
| :white_check_mark: | 2026-01-25 | Harper Rookie Rumble                          | TrackWrestling |
| :white_check_mark: | 2026-01-25 | LP Crunching Cavs Classic                     | TrackWrestling |
| :white_check_mark: | 2026-01-25 | Pekin Custer/Stoudt Open                      | TrackWrestling |
| :white_check_mark: | 2026-01-25 | Big Cat Wrestling Tournament                  | USA Bracketing |
| :white_check_mark: | 2026-01-25 | Spartan Rumble                                | USA Bracketing |
| :white_check_mark: | 2026-01-31 | 2026 IL Kids Future Finalist                  | TrackWrestling |
| :white_check_mark: | 2026-02-01 | 2026 Lemont Bears Bash                        | TrackWrestling |
| :white_check_mark: | 2026-02-01 | 2026 ST. CHARLES BATTLE FOR THE SHIELD        | TrackWrestling |
| :white_check_mark: | 2026-02-01 | Belvidere Bandit Brawl                        | TrackWrestling |
| :white_check_mark: | 2026-02-01 | Litchfield `Rumble In the Jungle` 2026        | TrackWrestling |
| :white_check_mark: | 2026-02-01 | Notre Dame Invitational                       | TrackWrestling |
| :white_check_mark: | 2026-02-01 | O-Town Throwdown 2026                         | TrackWrestling |
| :white_check_mark: | 2026-02-01 | QUINCY LITTLE RAIDER SLAM 2026                | TrackWrestling |
| :white_check_mark: | 2026-02-01 | Toultown Throwdown                            | TrackWrestling |
| :white_check_mark: | 2026-02-01 | Yorkville Fighting Foxes Invitational         | TrackWrestling |
| :white_check_mark: | 2026-02-01 | Cole Whitford Girls & Beginners Tournament    | USA Bracketing |
| :white_check_mark: | 2026-02-01 | IKWF Dual Meet State Championships            | USA Bracketing |
| :white_check_mark: | 2026-02-01 | Metamora Kids Wrestling Tournament            | USA Bracketing |
| :white_check_mark: | 2026-02-07 | Streator Bulldog Open                         | TrackWrestling |
| :white_check_mark: | 2026-02-08 | 2026 Derrick Munos Invitational               | TrackWrestling |
| :white_check_mark: | 2026-02-08 | 2026 Red Rush Rumble                          | TrackWrestling |
| :white_check_mark: | 2026-02-08 | 2026 shamrock slam                            | TrackWrestling |
| :white_check_mark: | 2026-02-08 | 2026 Ted Harvey Memorial                      | TrackWrestling |
| :white_check_mark: | 2026-02-08 | 2026 Triad Kids Open                          | TrackWrestling |
| :white_check_mark: | 2026-02-08 | AJ Jr Wildcats On the Prowl                   | TrackWrestling |
| :white_check_mark: | 2026-02-08 | Hononegah`s Tomahawk Classic                  | TrackWrestling |
| :white_check_mark: | 2026-02-08 | Warrensburg-Latham Cardinal Cradle Class      | TrackWrestling |
| :white_check_mark: | 2026-02-08 | Winter Fiesta @ Harper College                | TrackWrestling |
| :white_check_mark: | 2026-02-08 | Meet in the MIddle                            | USA Bracketing |
| :white_check_mark: | 2026-02-14 | 2026 O`Fallon Panther Pummel w/Girls          | TrackWrestling |
| :white_check_mark: | 2026-02-15 | 2026 BRONCO INVITE                            | TrackWrestling |
| :white_check_mark: | 2026-02-15 | 2026 Junior Thunderbolt                       | TrackWrestling |
| :white_check_mark: | 2026-02-15 | Cumberland Kids Heartbreak Havoc              | TrackWrestling |
| :white_check_mark: | 2026-02-15 | Daisy Fresh Wrestling Open                    | TrackWrestling |
| :white_check_mark: | 2026-02-15 | Olympia Spartan Showdown                      | TrackWrestling |
|                    | 2026-02-15 | ROUGHNECKS WRESTLING THROWDOWN                | TrackWrestling |
| :white_check_mark: | 2026-02-15 | Tiger Town Tanglers Wrestling Tournament      | TrackWrestling |
| :white_check_mark: | 2026-02-15 | Tri-County Polar Vortex                       | TrackWrestling |
| :white_check_mark: | 2026-02-15 | Wolves Wrestling St. Valentine`s Day Massacre | TrackWrestling |
| :white_check_mark: | 2026-02-22 | CLIPPER CLASH 2026                            | TrackWrestling |
| :white_check_mark: | 2026-02-22 | Heart of a Lion 2026                          | TrackWrestling |
| :white_check_mark: | 2026-02-22 | Jersey Panther Pummel                         | TrackWrestling |
| :white_check_mark: | 2026-02-22 | Peoria Heights Minutemen Kids Tournament      | TrackWrestling |
| :white_check_mark: | 2026-02-22 | Trico Pioneer Rumble                          | TrackWrestling |
| :white_check_mark: | 2026-02-22 | Champaign Grappler III                        | USA Bracketing |

## Data pipeline

```
uv run python -m entrypoints.parse_rosters  # Produces `_parsed-data/rosters.json`

uv run python -m entrypoints.fetch_trackwrestling
uv run python -m entrypoints.fetch_trackwrestling_duals
uv run python -m entrypoints.fetch_usabracketing
uv run python -m entrypoints.fetch_usabracketing_duals

uv run python -m entrypoints.parse_matches       # Produces `_parsed-data/all-matches-01.csv`
uv run python -m entrypoints.normalize_teams     # Produces `_parsed-data/all-matches-02.csv`
uv run python -m entrypoints.normalize_athletes  # Produces `_parsed-data/all-matches-03.csv`
uv run python -m entrypoints.normalize_weights   # Produces `_parsed-data/all-matches-04.csv`

uv run python -m entrypoints.sectional_brackets  # Produces `_parsed-data/{SECTIONAL}.xlsx`

uv run python -m entrypoints.regional_weights    # Produces `_parsed-data/regional-weights.xlsx`
uv run python -m entrypoints.regional_seeding \  # Produces per-regional sorted + head-to-heads
  --entries-filename ./weighed-in-entries.csv \
  --seeding-filename ./weight-classes.xlsx
```

[1]: https://www.ikwf.org/
[2]: https://docs.google.com/spreadsheets/d/1F_v5jk20rYQD8hZnzH7GGx_TfBLcXahDEiVbDKoxviA/edit
