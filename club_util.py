import pathlib
from typing import Literal

import pydantic

_HERE = pathlib.Path(__file__).resolve().parent


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
    return clubs_root.root
