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


def _add_wrestler(
    team: str,
    key: tuple[bracket_util.Division, int],
    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass],
    athlete: club_util.Athlete,
    matches: list[bracket_util.MatchV4],
    state_2025_note: str,
) -> None:
    if key not in weight_classes:
        weight_classes[key] = _WeightClass(athletes=[], head_to_heads=[])

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
        elif match_.loser_usaw_number == usaw_number:
            losses += 1
            if match_.winner_usaw_number in existing_usaw:
                weight_class.head_to_heads.append(match_)
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


class _Preview(_ForbidExtra):
    athletes: list[_PreviewAthlete]
    head_to_heads: list[_PreviewHeadToHead]


_Previews = dict[_PreviewDivision, dict[int, _Preview]]


class _PreviewsRoot(pydantic.RootModel[_Previews]):
    pass


def _make_weight_preview(
    weight_class: _WeightClass, team_to_sectional: dict[str, _PreviewSectional]
) -> _Preview:
    preview_athletes: list[_PreviewAthlete] = []
    preview_head_to_heads: list[_PreviewHeadToHead] = []

    athletes = _sort_by_record(weight_class.athletes)
    for athlete in athletes:
        preview_athletes.append(
            _PreviewAthlete(
                name=athlete.name,
                club=athlete.team,
                sectional=team_to_sectional[athlete.team],
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

    return _Preview(athletes=preview_athletes, head_to_heads=preview_head_to_heads)


def _weight_class_sort_func(key: tuple[bracket_util.Division, int]) -> tuple[int, int]:
    division, weight = key
    return bracket_util.sortable_division(division), weight


class _SectionalQualifier(_ForbidExtra):
    division: bracket_util.Division = pydantic.Field(alias="Division")
    weight: int = pydantic.Field(alias="Weight")
    name: str = pydantic.Field(alias="Name")
    club: str = pydantic.Field(alias="Club")
    usaw_number: str | None = pydantic.Field(alias="USAW Number")


class _SectionalQualifiers(pydantic.RootModel[list[_SectionalQualifier]]):
    pass


def _load_sectional_qualifiers() -> list[_SectionalQualifier]:
    input_file = _ROOT / "_parsed-data" / "sectional-qualifiers.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    for row in rows:
        if row["USAW Number"] == "":
            row["USAW Number"] = None

    qualifiers_root = _SectionalQualifiers.model_validate(rows)
    return qualifiers_root.root


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
    qualifier: _SectionalQualifier, athlete_matcher: _AthleteMatcher
) -> club_util.Athlete:
    team_matcher = athlete_matcher.get(qualifier.club)
    if team_matcher is None:
        raise ValueError("Missing team match", qualifier)

    if qualifier.usaw_number is not None:
        matches = [
            athlete
            for athlete in team_matcher.values()
            if athlete.usaw_number == qualifier.usaw_number
        ]
        if len(matches) != 1:
            raise ValueError("Missing athlete match", len(matches), qualifier)
        return matches[0]

    athlete = team_matcher.get(qualifier.name)
    if athlete is None:
        raise ValueError("Missing athlete match", qualifier)

    return athlete


def _resolve_all_usaw(
    sectional_qualifiers: list[_SectionalQualifier], athlete_matcher: _AthleteMatcher
) -> dict[str, tuple[_SectionalQualifier, club_util.Athlete]]:
    by_usaw_number: dict[str, tuple[_SectionalQualifier, club_util.Athlete]] = {}

    for qualifier in sectional_qualifiers:
        athlete = _get_athlete(qualifier, athlete_matcher)
        usaw_number = athlete.usaw_number
        if usaw_number in by_usaw_number:
            raise KeyError("Duplicate athlete", qualifier, usaw_number)

        by_usaw_number[usaw_number] = qualifier, athlete

    return by_usaw_number


def _generate_json_file(
    matches_v4: list[bracket_util.MatchV4],
    athlete_matcher: _AthleteMatcher,
    sectional_qualifiers: dict[str, tuple[_SectionalQualifier, club_util.Athlete]],
    state_qualifiers: dict[str, dict[str, club_util.StateQualifier]],
    team_to_sectional: dict[str, _PreviewSectional],
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

    weight_classes: dict[tuple[bracket_util.Division, int], _WeightClass] = {}
    for team, by_usaw in team_mapped.items():
        for usaw_number, matches in by_usaw.items():
            known = sectional_qualifiers.get(usaw_number)
            if known is None:
                continue

            qualifier, athlete = known
            key = qualifier.division, qualifier.weight

            state_2025_note = ""
            state_qualifier = state_qualifiers.get(team, {}).get(athlete.name)
            if state_qualifier is not None:
                state_2025_note = state_qualifier.result

            _add_wrestler(
                team,
                key,
                weight_classes,
                athlete,
                matches,
                state_2025_note,
            )

    keys = sorted(weight_classes.keys(), key=_weight_class_sort_func)
    previews: _Previews = {}
    for key in keys:
        weight_class = weight_classes[key]
        division, weight = key
        division_key = _translate_division(division)
        previews.setdefault(division_key, {})
        previews[division_key][weight] = _make_weight_preview(
            weight_class, team_to_sectional
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


def main() -> None:
    matches_v4 = projection.load_matches_v4()
    rosters = club_util.load_rosters()
    athlete_matcher = _make_athlete_matcher(rosters)
    state_qualifiers = club_util.load_state_qualifiers()
    sectional_qualifiers_list = _load_sectional_qualifiers()
    sectional_qualifiers = _resolve_all_usaw(sectional_qualifiers_list, athlete_matcher)
    team_to_sectional = _get_team_to_sectional(rosters)

    _generate_json_file(
        matches_v4,
        athlete_matcher,
        sectional_qualifiers,
        state_qualifiers,
        team_to_sectional,
    )


if __name__ == "__main__":
    main()
