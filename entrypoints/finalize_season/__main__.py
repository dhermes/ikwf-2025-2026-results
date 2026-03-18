import csv
import pathlib
from typing import Literal

import bs4
import pydantic

import bracket_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_WEIGHT_MARGIN_LEFT = "margin-left:0px"
_WRESTLER_MARGIN_LEFT = "margin-left:20px"
_EXPECTED_PLACES = ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th")
_TEAM_REPLACE: dict[str, str] = {}


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


_Sectional = Literal[
    "central",
    "central_chicago",
    "north",
    "north_chicago",
    "south",
    "south_chicago",
    "west",
    "west_chicago",
]


class _CSVStateQualifier(_ForbidExtra):
    division: bracket_util.Division = pydantic.Field(alias="Division")
    weight: int = pydantic.Field(alias="Weight")
    name: str = pydantic.Field(alias="Name")
    club: str = pydantic.Field(alias="Club")
    placement_sectional: str = pydantic.Field(alias="Placement")
    sectional: _Sectional = pydantic.Field(alias="Sectional")
    usaw_number: str = pydantic.Field(alias="USAW Number")


class _CSVStateQualifiers(pydantic.RootModel[list[_CSVStateQualifier]]):
    pass


def _load_csv_state_qualifiers() -> list[_CSVStateQualifier]:
    input_file = _ROOT / "_parsed-data" / "state-qualifiers.csv"
    with open(input_file) as file_obj:
        rows = list(csv.DictReader(file_obj))

    qualifiers_root = _CSVStateQualifiers.model_validate(rows)
    return qualifiers_root.root


def _get_margin_left_style(tag: bs4.Tag) -> str:
    style = tag.get("style", "")
    matches = [part for part in style.split(";") if part.startswith("margin-left:")]
    if len(matches) != 1:
        raise RuntimeError("Unexpected tag style", style)

    return matches[0]


def _reverse_division(division_str: str) -> bracket_util.Division:
    if division_str == "Boys Bantam":
        return "bantam"

    if division_str == "Boys Intermediate":
        return "intermediate"

    if division_str == "Boys Novice":
        return "novice"

    if division_str == "Boys Senior":
        return "senior"

    if division_str == "Girls Bantam":
        return "girls_bantam"

    if division_str == "Girls Intermediate":
        return "girls_intermediate"

    if division_str == "Girls Novice":
        return "girls_novice"

    if division_str == "Girls Senior":
        return "girls_senior"

    raise RuntimeError("Unsupported division", division_str)


def _parse_division_weight(div: bs4.Tag) -> tuple[bracket_util.Division, int]:
    division_str, weight_str = div.text.strip().split(" - ")
    weight = int(weight_str)
    division = _reverse_division(division_str)

    weights = bracket_util.weights_for_division(division)
    if weight not in weights:
        raise ValueError("Unexpected weight", div.text.strip())
    return division, weight


def _normalize_team(team: str) -> str:
    return _TEAM_REPLACE.get(team, team)


class _StateQualifierWithPlacement(_CSVStateQualifier):
    placement_state: str

    @classmethod
    def from_base(
        cls, inherit: _CSVStateQualifier, placement_state: str
    ) -> _StateQualifierWithPlacement:
        data = inherit.model_dump(mode="json")
        data["placement_state"] = placement_state
        return cls(**data)


def _parse_wrestler_div(
    div: bs4.Tag,
    division_weight: tuple[bracket_util.Division, int],
    roster_map: dict[str, dict[str, _CSVStateQualifier]],
) -> _StateQualifierWithPlacement:
    division, weight = division_weight

    place_athlete_team = div.text.strip()
    place, athlete_team = place_athlete_team.split(" - ", 1)
    if place not in _EXPECTED_PLACES:
        raise ValueError("Unexpected place", place_athlete_team)

    name, team = athlete_team.rsplit(" (", 1)
    if not team.endswith(")"):
        raise ValueError("Unexpected format", place_athlete_team)

    team = team[:-1]
    team_normalized = _normalize_team(team)

    athlete_map = roster_map.get(team_normalized)
    if athlete_map is None and team_normalized.endswith(" WC"):
        team_normalized = team_normalized[:-2] + "Wrestling Club"
        athlete_map = roster_map.get(team_normalized)

    if athlete_map is None:
        raise ValueError("Missing team", team, team_normalized)

    name_key = name.lower()
    qualifier = athlete_map.get(name_key)
    if qualifier is None:
        raise ValueError("Missing athlete", team_normalized, name)

    if qualifier.division != division or qualifier.weight != weight:
        raise ValueError("Invalid athlete", division, weight, qualifier)

    return _StateQualifierWithPlacement.from_base(qualifier, place)


def _get_state_placements(
    roster_map: dict[str, dict[str, _CSVStateQualifier]],
) -> dict[str, _StateQualifierWithPlacement]:
    input_file = _ROOT / "_raw-data" / "state-final-placements" / "state.html"
    with open(input_file) as file_obj:
        html = file_obj.read()

    soup = bs4.BeautifulSoup(html, features="html.parser")
    (parent_div,) = soup.find_all("div", style="font-size:12pt;")
    direct_divs = parent_div.find_all("div", recursive=False)

    division_weight: tuple[bracket_util.Division, int] | None = None
    placers: dict[str, _StateQualifierWithPlacement] = {}
    for div in direct_divs:
        margin_left = _get_margin_left_style(div)
        if margin_left == _WEIGHT_MARGIN_LEFT:
            division_weight = _parse_division_weight(div)
            continue

        if margin_left == _WRESTLER_MARGIN_LEFT:
            if division_weight is None:
                raise ValueError("Expected a division weight already", div)

            placer = _parse_wrestler_div(div, division_weight, roster_map)
            if placer.usaw_number in placers:
                raise KeyError("Duplicate placer", placer.usaw_number)
            placers[placer.usaw_number] = placer
            continue

        raise RuntimeError("Unexpected margin", div)

    return placers


class _StateQualifiersWithPlacement(
    pydantic.RootModel[list[_StateQualifierWithPlacement]]
):
    pass


def main() -> None:
    state_qualifiers = _load_csv_state_qualifiers()

    roster_map: dict[str, dict[str, _CSVStateQualifier]] = {}
    for state_qualifier in state_qualifiers:
        club = state_qualifier.club
        roster_map.setdefault(club, {})
        name_key = state_qualifier.name.lower()
        if name_key in roster_map:
            raise KeyError("Duplicate name", club, name_key)
        roster_map[club][name_key] = state_qualifier

    state_placements = _get_state_placements(roster_map)

    with_placements: list[_StateQualifierWithPlacement] = []
    for state_qualifier in state_qualifiers:
        with_placement = state_placements.get(state_qualifier.usaw_number)
        if with_placement is None:
            with_placement = _StateQualifierWithPlacement.from_base(state_qualifier, "")
        with_placements.append(with_placement)

    to_serialize = _StateQualifiersWithPlacement(root=with_placements)

    final_filename = _ROOT / "_parsed-data" / "2026-finalized.json"
    as_json = to_serialize.model_dump_json(indent=2)
    with open(final_filename, "w") as file_obj:
        file_obj.write(as_json)
        file_obj.write("\n")


if __name__ == "__main__":
    main()
