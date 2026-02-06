import pathlib
from typing import Literal

import pydantic

_HERE = pathlib.Path(__file__).resolve().parent
_IGNORED_ATHLETES: dict[str, list[str]] = {
    "MS Youth Wrestling Club": [
        # NOTE: `Owen Miller` also shows up as a 10 year old for same club
        "2405967201",
    ],
    "Oak Forest Park District Warriors Wrestling": [
        # NOTE: `Oliver McCormies` has two USAW numbers, both age 9
        "2606969201",
    ],
    "Litchfield Wrestling Club": [
        # NOTE: `Silas Hogue` has two USAW numbers, both age 9
        "2609186701",
    ],
}


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")


class Athlete(_ForbidExtra):
    usaw_number: str
    name: str
    ikwf_age: int


Sectional = Literal[
    "Central",
    "North",
    "South",
    "West",
    "Central Chicago",
    "North Chicago",
    "South Chicago",
    "West Chicago",
]


class ClubInfo(_ForbidExtra):
    club_name: str
    sectional: Sectional
    athletes: list[Athlete]


class Clubs(pydantic.RootModel[list[ClubInfo]]):
    pass


class _CustomTeamNameMap(pydantic.RootModel[dict[str, str]]):
    pass


def load_custom_team_name_map() -> dict[str, str]:
    path = _HERE / "_parsed-data" / "custom-normalized-team-names.json"
    with open(path, "rb") as file_obj:
        as_json = file_obj.read()

    root = _CustomTeamNameMap.model_validate_json(as_json)
    return root.root


def load_rosters() -> list[ClubInfo]:
    input_file = _HERE / "_parsed-data" / "rosters.json"
    with open(input_file) as file_obj:
        as_json = file_obj.read()

    clubs_root = Clubs.model_validate_json(as_json)

    result = clubs_root.root
    for club_info in result:
        ignored_for_team = _IGNORED_ATHLETES.get(club_info.club_name)
        if ignored_for_team is None:
            continue

        athletes_keep = [
            athlete
            for athlete in club_info.athletes
            if athlete.usaw_number not in ignored_for_team
        ]
        club_info.athletes = athletes_keep

    return result


class _CustomAthleteNameMap(pydantic.RootModel[dict[str, dict[str, str | None]]]):
    pass


def load_custom_athlete_name_map() -> dict[str, dict[str, str | None]]:
    path = _HERE / "_parsed-data" / "custom-normalized-athlete-names.json"
    with open(path, "rb") as file_obj:
        as_json = file_obj.read()

    root = _CustomAthleteNameMap.model_validate_json(as_json)
    return root.root


class StateQualifier(_ForbidExtra):
    ikwf_age: int
    result: str
    team_2025: str
    usaw_number: str


class _StateQualifiers(pydantic.RootModel[dict[str, dict[str, StateQualifier]]]):
    pass


def load_state_qualifiers() -> dict[str, dict[str, StateQualifier]]:
    path = _HERE / "_parsed-data" / "2026-rostered-state-qualifiers.json"
    with open(path, "rb") as file_obj:
        as_json = file_obj.read()

    root = _StateQualifiers.model_validate_json(as_json)
    return root.root
