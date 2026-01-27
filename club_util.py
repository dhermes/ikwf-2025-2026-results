from typing import Literal

import pydantic


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
