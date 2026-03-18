import csv
import datetime
import pathlib
from typing import Literal

import pydantic

import bracket_util
import club_util
import projection

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_TEAM_LAST_RESORT: dict[tuple[str, str], str] = {
    ("Beat the Streets Chi", "Makai Dike"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Alex Champ"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Alexa Nunn"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Allison Quiroz"): "Beat the Streets Chicago-Midway",
    (
        "Beat the Streets Chi",
        "Andrew Ayala-Mendoz",
    ): "Beat the Streets Chicago-Tri Taylor",
    ("Beat the Streets Chi", "Bobby Corey"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Brazil Moore"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Camila S Rodriguez"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Carlos Azevedo"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Carola Garduno-Diaz"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Carter Winston"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Ce'Ana Lee"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Ce'Nia Lee"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Corey Stuckey-Blan"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Damien Givhan"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Daniela Venegas"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Diarmaid McGuire"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Diego Navarro"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Eli Ivory"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Eliana Ortega"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Elias Vizcarra"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Elijah Carter"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Emyr Kelly"): "Beat the Streets Chicago-Roseland",
    (
        "Beat the Streets Chi",
        "Esteban Castellanos",
    ): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Ethan Gholston"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Gabby guaman"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Gemma Hernandez"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Giuseppe Perez"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Isaac Aronson"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Isaiah Morquecho"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Itzel Fortiz"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Jack Wahtola"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Jacqueli Recendez"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Jade Lee"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Jade Zambrano"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Jaden Washington"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "January Powell"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Jelena Cisneros - D"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Jeremiya Winn"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Jezrah Lopez Hernan"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Jordan Qualkinbush"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Journee Gholston"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Joy Lee"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Keithen Rice"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Kenzee Wildt"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Kori Smith"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Libby Gagen"): "Beat the Streets Chicago-Tri Taylor",
    ("Beat the Streets Chi", "Louisa Dies"): "Beat the Streets Chicago-Tri Taylor",
    ("Beat the Streets Chi", "Luca Paolella"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Mason Glanville"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Matteo Russo"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Mincere White"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Molly Gagen"): "Beat the Streets Chicago-Tri Taylor",
    ("Beat the Streets Chi", "Natalia Ferguson"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Noah Reyes"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Olive Gagen"): "Beat the Streets Chicago-Tri Taylor",
    ("Beat the Streets Chi", "Oliver Smart"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Scarlett Reyes"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Sebastia Cubillos"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Sincere Staples"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Sloane Araujo"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Victor Vargas"): "Beat the Streets Chicago-Oak Park",
    ("Beat the Streets Chi", "Vivienne Nichols"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Xavier Yankellow"): "Beat the Streets Chicago-Avondale",
    ("Beat the Streets Chi", "Yaili Fortiz"): "Beat the Streets Chicago-Midway",
    ("Beat the Streets Chi", "Zairah West"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Zephania Powell"): "Beat the Streets Chicago-Roseland",
    ("Beat the Streets Chi", "Zoey Rousseau"): "Beat the Streets Chicago-Midway",
}
_NAME_FIX: dict[str, dict[str, str]] = {
    "Astro Wrestling Club": {"Dai Zari Christopher": "Dai Zaria Christopher"},
    "Badger Wrestling Club": {"Luz Guerra Gonza": "Luz Guerra Gonzalez"},
    "Beat the Streets Chicago-Midway": {
        "Jelena Cisneros - D": "Jelena Cisneros - Diaz",
        "Jezrah Lopez Hernan": "Jezrah Lopez Hernandez",
    },
    "Doom Wrestling": {"Dylan Ra Perkins": "Dylan Rae Perkins"},
    "Eureka Wrestling Club": {"Josie Skelton": "Josie skelton"},
    "Harlem Huskies WC": {"Shawn Ma Omeara": "Shawn Marie Omeara"},
    "Junior Kahoks-Tribe Fellowship": {"Alta Jan McQuary": "Alta Jane McQuary"},
    "Lockport Junior Porters WC": {"Elise Voight": "elise voight"},
    "Rockets Wrestling Club": {"Andrea Vences": "ANDREA VENCES"},
    "Storm Youth Wrestling Club": {
        "Pedro Da Rangel": "Pedro David Rangel",
        "Pedro Le Rangel": "Pedro Legend Rangel",
    },
    "Sycamore Wrestling Club": {"Mary Jan Watie": "Mary Jane Watie"},
}


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class _WeightAthlete(_ForbidExtra):
    usaw_number: str
    name: str
    ikwf_age: int
    team: str
    wins: pydantic.NonNegativeInt
    losses: pydantic.NonNegativeInt
    matches: list[bracket_util.MatchV4]
    state_2025_note: str


class _WeightClass(_ForbidExtra):
    athletes: list[_WeightAthlete]
    head_to_heads: list[bracket_util.MatchV4]
    against_other_qualifiers: list[bracket_util.MatchV4]


def _add_wrestler(
    team: str,
    key: tuple[bracket_util.Division, int],
    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass],
    athlete: club_util.Athlete,
    matches: list[bracket_util.MatchV4],
    state_2025_note: str,
    entire_field: dict[str, tuple[bracket_util.Division, int]],
) -> None:
    if key not in weight_classes:
        weight_classes[key] = _WeightClass(
            athletes=[],
            head_to_heads=[],
            against_other_qualifiers=[],
        )

    weight_class = weight_classes[key]
    existing_usaw = set(
        [other_athlete.usaw_number for other_athlete in weight_class.athletes]
    )

    usaw_number = athlete.usaw_number
    wins = 0
    losses = 0
    for match_ in matches:
        if match_.winner_usaw_number == usaw_number:
            wins += 1
            if match_.loser_usaw_number in existing_usaw:
                weight_class.head_to_heads.append(match_)
            elif entire_field.get(match_.loser_usaw_number, key) != key:
                weight_class.against_other_qualifiers.append(match_)
        elif match_.loser_usaw_number == usaw_number:
            losses += 1
            if match_.winner_usaw_number in existing_usaw:
                weight_class.head_to_heads.append(match_)
            elif entire_field.get(match_.winner_usaw_number, key) != key:
                weight_class.against_other_qualifiers.append(match_)
        else:
            raise RuntimeError("Unexpected match", match_, usaw_number)

    weight_class.athletes.append(
        _WeightAthlete(
            usaw_number=athlete.usaw_number,
            name=athlete.name,
            ikwf_age=athlete.ikwf_age,
            team=team,
            wins=wins,
            losses=losses,
            matches=matches,
            state_2025_note=state_2025_note,
        )
    )


def _sort_helper(athlete: _WeightAthlete) -> float:
    wins = athlete.wins
    losses = athlete.losses

    matches = wins + losses

    # NOTE: Assume a previous record of 5-5 to penalize low match counts while
    #       not materially changing the sorting of 16-5 vs. 12-8
    return (wins + 5) / (matches + 10)


def _sort_by_record(athletes: list[_WeightAthlete]) -> list[_WeightAthlete]:
    return sorted(athletes, key=_sort_helper, reverse=True)


_PreviewDivision = Literal[
    "bantam",
    "intermediate",
    "novice",
    "senior",
    "bantam_girls",
    "intermediate_girls",
    "novice_girls",
    "senior_girls",
]

_PreviewSectional = Literal[
    "central",
    "central_chicago",
    "north",
    "north_chicago",
    "south",
    "south_chicago",
    "west",
    "west_chicago",
]


class _PreviewAthlete(_ForbidExtra):
    name: str
    club: str
    sectional: _PreviewSectional
    sectional_placement: str | None
    wins: int
    losses: int
    ikwf_age: int
    state_result_2025: str | None


class _PreviewHeadToHead(_ForbidExtra):
    winner: str
    winner_club: str
    winner_sectional: _PreviewSectional
    loser: str
    loser_club: str
    loser_sectional: _PreviewSectional
    result: str
    event_date: datetime.date


class _PreviewHeadToHeadExtra(_PreviewHeadToHead):
    other_division: _PreviewDivision
    other_weight: int


class _SimpleAthlete(_ForbidExtra):
    name: str
    club: str


class _Preview(_ForbidExtra):
    athletes: list[_PreviewAthlete]
    head_to_heads: list[_PreviewHeadToHead]
    bracket_slots: list[_SimpleAthlete | None]
    against_other_qualifiers: list[_PreviewHeadToHeadExtra]


_Previews = dict[_PreviewDivision, dict[int, _Preview]]


class _PreviewsRoot(pydantic.RootModel[_Previews]):
    pass


def _head_to_head_sort_func(match_: _PreviewHeadToHead) -> tuple[int, str, str]:
    return -match_.event_date.toordinal(), match_.winner, match_.loser


def _resolve_simple_athlete_club(
    club: str, name: str, by_club: dict[str, list[str]]
) -> str:
    if club in by_club:
        return club

    matches = [key for key in by_club if key.startswith(club)]
    if len(matches) == 1:
        return matches[0]

    club_edited = club
    if club.endswith(" WC"):
        club_edited = club[:-2] + "Wrestling Club"

    if club_edited in by_club:
        return club_edited

    key = (club, name)
    if key in _TEAM_LAST_RESORT:
        return _TEAM_LAST_RESORT[key]

    raise ValueError("Could not resolve club", club, name)


def _to_shorter_names_simple(club_athletes: list[str]) -> dict[str, str]:
    shorter_names: dict[str, str] = {}
    for name in club_athletes:
        first_name, remaining = name.split(" ", 1)
        # NOTE: The presentation cuts off first names at 8 characters
        first_name = first_name[:8]
        if " " not in remaining:
            # NOTE: The presentation cuts off last names at 12 characters
            remaining = remaining[:12]

        shortened = f"{first_name} {remaining}"
        shortened = shortened.lower()
        if shortened in shorter_names:
            raise ValueError("Duplicate short name", shortened)
        shorter_names[shortened] = name

    return shorter_names


def _resolve_simple_athlete_name(club: str, name: str, club_athletes: list[str]) -> str:
    if name in club_athletes:
        return name

    fixes = _NAME_FIX.get(club, {})
    if name in fixes:
        return fixes[name]

    shorter_names = _to_shorter_names_simple(club_athletes)
    if name.lower() in shorter_names:
        return shorter_names[name.lower()]

    raise ValueError("Could not resolve name", club, name)


def _to_simple_athlete(
    entry: _Entry | None, preview_athletes: list[_PreviewAthlete]
) -> _SimpleAthlete | None:
    if entry is None:
        return None

    by_club: dict[str, list[str]] = {}
    for preview_athlete in preview_athletes:
        club = preview_athlete.club
        by_club.setdefault(club, [])
        by_club[club].append(preview_athlete.name)

    # NOTE: This is suboptimal, but this is throwaway code only needed for a
    #       few days during state week.
    club = _resolve_simple_athlete_club(entry.team, entry.name, by_club)
    club_athletes = by_club[club]
    name = _resolve_simple_athlete_name(club, entry.name, club_athletes)

    return _SimpleAthlete(name=name, club=club)


def _make_weight_preview(
    weight_class: _WeightClass,
    team_to_sectional: dict[str, _PreviewSectional],
    state_entry_weight: _ScrapedWeightClass,
    placement_by_usaw: dict[str, str],
    entire_field: dict[str, tuple[bracket_util.Division, int]],
) -> _Preview:
    preview_athletes: list[_PreviewAthlete] = []
    preview_head_to_heads: list[_PreviewHeadToHead] = []

    usaw_in_weight: set[str] = set()

    athletes = _sort_by_record(weight_class.athletes)
    for athlete in athletes:
        usaw_in_weight.add(athlete.usaw_number)
        placement = placement_by_usaw.get(athlete.usaw_number)
        preview_athletes.append(
            _PreviewAthlete(
                name=athlete.name,
                club=athlete.team,
                sectional=team_to_sectional[athlete.team],
                sectional_placement=placement,
                wins=athlete.wins,
                losses=athlete.losses,
                ikwf_age=athlete.ikwf_age,
                state_result_2025=athlete.state_2025_note or None,
            )
        )

    for match_ in weight_class.head_to_heads:
        preview_head_to_heads.append(
            _PreviewHeadToHead(
                winner=match_.winner_normalized,
                winner_club=match_.winner_team_normalized,
                winner_sectional=team_to_sectional[match_.winner_team_normalized],
                loser=match_.loser_normalized,
                loser_club=match_.loser_team_normalized,
                loser_sectional=team_to_sectional[match_.loser_team_normalized],
                result=match_.result,
                event_date=match_.event_date,
            )
        )

    preview_head_to_heads.sort(key=_head_to_head_sort_func)
    if len(state_entry_weight.entries) != 24:
        raise RuntimeError("Unexpected bracket", state_entry_weight)
    bracket_slots: list[_SimpleAthlete | None] = [
        _to_simple_athlete(entry, preview_athletes)
        for entry in state_entry_weight.entries
    ]

    preview_against_other: list[_PreviewHeadToHead] = []
    for match_ in weight_class.against_other_qualifiers:
        if match_.winner_usaw_number in usaw_in_weight:
            other = entire_field.get(match_.loser_usaw_number)
            if other is None:
                raise ValueError("Missing other wrestling", match_)
            other_division, other_weight = other
        elif match_.loser_usaw_number in usaw_in_weight:
            other = entire_field.get(match_.winner_usaw_number)
            if other is None:
                raise ValueError("Missing other wrestling", match_)
            other_division, other_weight = other
        else:
            raise ValueError("Match should not be in against other", match_)

        preview_against_other.append(
            _PreviewHeadToHeadExtra(
                winner=match_.winner_normalized,
                winner_club=match_.winner_team_normalized,
                winner_sectional=team_to_sectional[match_.winner_team_normalized],
                loser=match_.loser_normalized,
                loser_club=match_.loser_team_normalized,
                loser_sectional=team_to_sectional[match_.loser_team_normalized],
                result=match_.result,
                event_date=match_.event_date,
                other_division=_translate_division(other_division),
                other_weight=other_weight,
            )
        )
    preview_against_other.sort(key=_head_to_head_sort_func)

    return _Preview(
        athletes=preview_athletes,
        head_to_heads=preview_head_to_heads,
        bracket_slots=bracket_slots,
        against_other_qualifiers=preview_against_other,
    )


def _weight_class_sort_func(key: tuple[bracket_util.Division, int]) -> tuple[int, int]:
    division, weight = key
    return bracket_util.sortable_division(division), weight


class _StateQualifier(_ForbidExtra):
    division: bracket_util.Division
    weight: int
    name: str
    club: str


class _Entry(_ForbidExtra):
    name: str
    team: str


class _ScrapedWeightClass(_ForbidExtra):
    division: bracket_util.Division
    weight: int
    entries: list[_Entry | None]


class _ScrapedWeightClasses(pydantic.RootModel[list[_ScrapedWeightClass]]):
    pass


def _load_state_entries() -> list[_ScrapedWeightClass]:
    input_file = _ROOT / "_raw-data" / "bracket-parsing" / "state-entries.json"
    with open(input_file, "rb") as file_obj:
        content = file_obj.read()

    weight_classes = _ScrapedWeightClasses.model_validate_json(content)
    return weight_classes.root


_AthleteMatcher = dict[str, dict[str, club_util.Athlete]]


def _make_athlete_matcher(rosters: list[club_util.ClubInfo]) -> _AthleteMatcher:
    athlete_matcher: _AthleteMatcher = {}

    for roster in rosters:
        if roster.club_name in athlete_matcher:
            raise KeyError("Unexpected duplicate", roster.club_name)
        athlete_matcher[roster.club_name] = {}

        for athlete in roster.athletes:
            if athlete.name in athlete_matcher[roster.club_name]:
                raise KeyError("Unexpected duplicate", athlete)
            athlete_matcher[roster.club_name][athlete.name] = athlete

    return athlete_matcher


def _get_athlete(
    qualifier: _StateQualifier, athlete_matcher: _AthleteMatcher
) -> club_util.Athlete:
    team_matcher = athlete_matcher.get(qualifier.club)
    if team_matcher is None:
        raise ValueError("Missing team match", qualifier)

    athlete = team_matcher.get(qualifier.name)
    if athlete is None:
        raise ValueError("Missing athlete match", qualifier)

    return athlete


def _resolve_team(team: str, name: str, athlete_matcher: _AthleteMatcher) -> str:
    if team in athlete_matcher:
        return team

    matches = [key for key in athlete_matcher if key.startswith(team)]
    if len(matches) == 1:
        return matches[0]

    team_edited = team
    if team.endswith(" WC"):
        team_edited = team[:-2] + "Wrestling Club"

    if team_edited in athlete_matcher:
        return team_edited

    key = (team, name)
    if key in _TEAM_LAST_RESORT:
        return _TEAM_LAST_RESORT[key]

    raise ValueError("Could not resolve team", team, name)


def _to_shorter_names(team_athletes: dict[str, club_util.Athlete]) -> dict[str, str]:
    shorter_names: dict[str, str] = {}
    for name in team_athletes:
        first_name, remaining = name.split(" ", 1)
        # NOTE: The presentation cuts off first names at 8 characters
        first_name = first_name[:8]
        if " " not in remaining:
            # NOTE: The presentation cuts off last names at 12 characters
            remaining = remaining[:12]

        shortened = f"{first_name} {remaining}"
        shortened = shortened.lower()
        if shortened in shorter_names:
            raise ValueError("Duplicate short name", shortened)
        shorter_names[shortened] = name

    return shorter_names


def _resolve_name(
    team: str, name: str, team_athletes: dict[str, club_util.Athlete]
) -> str:
    if name in team_athletes:
        return name

    fixes = _NAME_FIX.get(team, {})
    if name in fixes:
        return fixes[name]

    shorter_names = _to_shorter_names(team_athletes)
    if name.lower() in shorter_names:
        return shorter_names[name.lower()]

    raise ValueError("Could not resolve name", team, name)


def _resolve_to_roster(
    weight_class: _WeightClass, entry: _Entry, athlete_matcher: _AthleteMatcher
) -> _StateQualifier:
    team = _resolve_team(entry.team, entry.name, athlete_matcher)
    team_athletes = athlete_matcher[team]
    name = _resolve_name(team, entry.name, team_athletes)

    return _StateQualifier(
        division=weight_class.division, weight=weight_class.weight, name=name, club=team
    )


def _resolve_all_usaw(
    state_entry_weights: list[_ScrapedWeightClass], athlete_matcher: _AthleteMatcher
) -> dict[str, tuple[_StateQualifier, club_util.Athlete]]:
    by_usaw_number: dict[str, tuple[_StateQualifier, club_util.Athlete]] = {}

    for weight_class in state_entry_weights:
        for entry in weight_class.entries:
            if entry is None:
                continue

            qualifier = _resolve_to_roster(weight_class, entry, athlete_matcher)
            athlete = _get_athlete(qualifier, athlete_matcher)
            usaw_number = athlete.usaw_number
            if usaw_number in by_usaw_number:
                raise KeyError("Duplicate athlete", qualifier, usaw_number)

            by_usaw_number[usaw_number] = qualifier, athlete

    return by_usaw_number


def _generate_json_file(
    matches_v4: list[bracket_util.MatchV4],
    athlete_matcher: _AthleteMatcher,
    state_qualifiers: dict[str, tuple[_StateQualifier, club_util.Athlete]],
    previous_state_qualifiers: dict[str, dict[str, club_util.StateQualifier]],
    team_to_sectional: dict[str, _PreviewSectional],
    state_entry_weights: list[_ScrapedWeightClass],
    placement_by_usaw: dict[str, str],
) -> None:
    team_names = set(athlete_matcher.keys())

    relevant_matches = [
        match_
        for match_ in matches_v4
        if (
            match_.winner_team_normalized in team_names
            or match_.loser_team_normalized in team_names
        )
    ]
    team_mapped = projection.map_by_team(relevant_matches, team_names)

    entire_field: dict[str, tuple[bracket_util.Division, int]] = {}
    for usaw_number, (qualifier, _) in state_qualifiers.items():
        entire_field[usaw_number] = qualifier.division, qualifier.weight

        # NOTE: Ensure all wrestlers are present, even those without matches
        if usaw_number in team_mapped[qualifier.club]:
            continue

        team_mapped[qualifier.club][usaw_number] = []

    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass] = {}
    for team, by_usaw in team_mapped.items():
        for usaw_number, matches in by_usaw.items():
            known = state_qualifiers.get(usaw_number)
            if known is None:
                continue

            qualifier, athlete = known
            key = qualifier.division, qualifier.weight

            state_2025_note = ""
            state_qualifier = previous_state_qualifiers.get(team, {}).get(athlete.name)
            if state_qualifier is not None:
                state_2025_note = state_qualifier.result

            _add_wrestler(
                team,
                key,
                weight_classes,
                athlete,
                matches,
                state_2025_note,
                entire_field,
            )

    keys = sorted(weight_classes.keys(), key=_weight_class_sort_func)
    previews: _Previews = {}
    for key in keys:
        weight_class = weight_classes[key]
        division, weight = key
        division_key = _translate_division(division)
        previews.setdefault(division_key, {})
        (state_entry_weight,) = [
            candidate
            for candidate in state_entry_weights
            if candidate.weight == weight and candidate.division == division
        ]
        previews[division_key][weight] = _make_weight_preview(
            weight_class,
            team_to_sectional,
            state_entry_weight,
            placement_by_usaw,
            entire_field,
        )

    previews_root = _PreviewsRoot(root=previews)
    as_json = previews_root.model_dump_json(indent=2)
    filename = _ROOT / "_parsed-data" / "2026-state-preview.json"
    with open(filename, "w") as file_obj:
        file_obj.write(as_json)
        file_obj.write("\n")


def _translate_division(division: bracket_util.Division) -> _PreviewDivision:
    if division == "bantam":
        return "bantam"
    if division == "intermediate":
        return "intermediate"
    if division == "novice":
        return "novice"
    if division == "senior":
        return "senior"
    if division == "girls_bantam":
        return "bantam_girls"
    if division == "girls_intermediate":
        return "intermediate_girls"
    if division == "girls_novice":
        return "novice_girls"
    if division == "girls_senior":
        return "senior_girls"

    raise NotImplementedError(division)


def _translate_sectional(sectional: club_util.Sectional) -> _PreviewSectional:
    if sectional == "Central":
        return "central"
    if sectional == "North":
        return "north"
    if sectional == "South":
        return "south"
    if sectional == "West":
        return "west"
    if sectional == "Central Chicago":
        return "central_chicago"
    if sectional == "North Chicago":
        return "north_chicago"
    if sectional == "South Chicago":
        return "south_chicago"
    if sectional == "West Chicago":
        return "west_chicago"

    raise NotImplementedError(sectional)

    return ""


def _get_team_to_sectional(
    rosters: list[club_util.ClubInfo],
) -> dict[str, _PreviewSectional]:
    team_to_sectional: dict[str, _PreviewSectional] = {}
    for roster in rosters:
        if roster.club_name in team_to_sectional:
            raise KeyError("Duplicate team", roster.club_name)
        team_to_sectional[roster.club_name] = _translate_sectional(roster.sectional)
    return team_to_sectional


class _CSVStateQualifier(_ForbidExtra):
    division: bracket_util.Division = pydantic.Field(alias="Division")
    weight: int = pydantic.Field(alias="Weight")
    name: str = pydantic.Field(alias="Name")
    club: str = pydantic.Field(alias="Club")
    placement: str = pydantic.Field(alias="Placement")
    sectional: _PreviewSectional = pydantic.Field(alias="Sectional")
    usaw_number: str = pydantic.Field(alias="USAW Number")


class _CSVStateQualifiers(pydantic.RootModel[list[_CSVStateQualifier]]):
    pass


def _load_csv_state_qualifiers() -> list[_CSVStateQualifier]:
    input_file = _ROOT / "_parsed-data" / "state-qualifiers.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    qualifiers_root = _CSVStateQualifiers.model_validate(rows)
    return qualifiers_root.root


def main() -> None:
    matches_v4 = projection.load_matches_v4()
    rosters = club_util.load_rosters()
    athlete_matcher = _make_athlete_matcher(rosters)
    previous_state_qualifiers = club_util.load_state_qualifiers()
    state_entry_weights = _load_state_entries()
    state_qualifiers = _resolve_all_usaw(state_entry_weights, athlete_matcher)
    team_to_sectional = _get_team_to_sectional(rosters)

    csv_state_qualifiers = _load_csv_state_qualifiers()
    placement_by_usaw: dict[str, str] = {}
    for csv_state_qualifier in csv_state_qualifiers:
        usaw_number = csv_state_qualifier.usaw_number
        if usaw_number in placement_by_usaw:
            raise ValueError("Duplicate USAW placement", usaw_number)
        placement_by_usaw[usaw_number] = csv_state_qualifier.placement

    _generate_json_file(
        matches_v4,
        athlete_matcher,
        state_qualifiers,
        previous_state_qualifiers,
        team_to_sectional,
        state_entry_weights,
        placement_by_usaw,
    )


if __name__ == "__main__":
    main()
