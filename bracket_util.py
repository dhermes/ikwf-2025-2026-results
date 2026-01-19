import datetime
import re
from typing import Literal

import pydantic

CSV_FIELD_NAMES = (
    "Event Name",
    "Event Date",
    "Bracket",
    "Round",
    "Division",
    "Winner",
    "Winner Team",
    "Loser",
    "Loser Team",
    "Result",
    "Result Type",
    "Source",
)


def to_kebab_case(name: str) -> str:
    # Lowercase
    name = name.lower()

    # Remove special characters
    name = re.sub(r"[.`~!@#$%^&*()=+\[\]{}\\|;:'\",<>/?]", "", name)

    # Replace spaces or underscores with hyphen
    name = re.sub(r"[ _]+", "-", name)

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    # Strip leading/trailing hyphens
    name = name.strip("-")

    return name


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class Tournament(_ForbidExtra):
    name: str
    start_date: datetime.date | None
    end_date: datetime.date


Division = Literal[
    "tot",
    "bantam",
    "intermediate",
    "novice",
    "senior",
    "girls_tot",
    "girls_bantam",
    "girls_intermediate",
    "girls_novice",
    "girls_senior",
]
ResultType = Literal["decision", "major", "tech", "pin", "overtime"]
Source = Literal[
    "trackwrestling", "trackwrestling_dual", "usabracketing", "usabracketing_dual"
]


class Match(_ForbidExtra):
    event_name: str = pydantic.Field(alias="Event Name")
    event_date: datetime.date = pydantic.Field(alias="Event Date")
    bracket: str = pydantic.Field(alias="Bracket")
    round_: str = pydantic.Field(alias="Round")
    division: Division | None = pydantic.Field(alias="Division")
    winner: str = pydantic.Field(alias="Winner")
    winner_team: str = pydantic.Field(alias="Winner Team")
    loser: str = pydantic.Field(alias="Loser")
    loser_team: str = pydantic.Field(alias="Loser Team")
    result: str = pydantic.Field(alias="Result")
    result_type: ResultType = pydantic.Field(alias="Result Type")
    source: Source = pydantic.Field(alias="Source")


def classify_bracket(name: str) -> Division | None:
    name_normalized = name.lower()

    if name_normalized.startswith("girls tot "):
        return "girls_tot"
    if name_normalized.startswith("girls tots "):
        return "girls_tot"
    if name_normalized.startswith("girls - tot "):
        return "girls_tot"

    if name_normalized.startswith("girls bantam "):
        return "girls_bantam"
    if name_normalized.startswith("girls 8u "):
        return "girls_bantam"
    if name_normalized.startswith("girls - bantam "):
        return "girls_bantam"
    if name_normalized.startswith("girls - bantams "):
        return "girls_bantam"
    if name_normalized.startswith("rookie girls bantam "):
        return "girls_bantam"
    if name_normalized.startswith("girls(6 -8) "):
        return "girls_bantam"
    if name_normalized.startswith("girls (6 - 8) "):
        return "girls_bantam"

    if name_normalized.startswith("girls intermediate "):
        return "girls_intermediate"
    if name_normalized.startswith("girls - intermediate "):
        return "girls_intermediate"
    if name_normalized.startswith("girls - intermediates "):
        return "girls_intermediate"
    if name_normalized.startswith("rookie girls intermediate "):
        return "girls_intermediate"
    if name_normalized.startswith("girls 10u "):
        return "girls_intermediate"

    if name_normalized.startswith("girls novice "):
        return "girls_novice"
    if name_normalized.startswith("girls - novice "):
        return "girls_novice"
    if name_normalized.startswith("rookie girls novice "):
        return "girls_novice"
    if name_normalized.startswith("girls 12u "):
        return "girls_novice"

    if name_normalized.startswith("girls senior "):
        return "girls_senior"
    if name_normalized.startswith("girls seniors "):
        return "girls_senior"
    if name_normalized.startswith("girls - seniors "):
        return "girls_senior"
    if name_normalized.startswith("girls - senior "):
        return "girls_senior"
    if name_normalized.startswith("girls (12 - 14) "):
        return "girls_senior"
    if name_normalized.startswith("elite girls "):
        return "girls_senior"
    if name_normalized.startswith("girls 14u "):
        return "girls_senior"

    ############################################################################

    if name_normalized.startswith("tot "):
        return "tot"
    if name_normalized.startswith("tot "):
        return "tot"
    if name_normalized.startswith("tot:"):
        return "tot"
    if name_normalized.startswith("open (tot) "):
        return "tot"
    if name_normalized.startswith("tots "):
        return "tot"
    if name_normalized.startswith("boys - tots "):
        return "tot"
    if name_normalized.startswith("tots("):
        return "tot"
    if name_normalized.startswith("6u "):
        return "tot"
    if name_normalized.startswith("5&6 "):
        return "tot"
    if name_normalized.startswith("6&u "):
        return "tot"

    if name_normalized.startswith("bantam "):
        return "bantam"
    if name_normalized.startswith("bantams "):
        return "bantam"
    if name_normalized.startswith("bantam-"):
        return "bantam"
    if name_normalized.startswith("bantam: "):
        return "bantam"
    if name_normalized.startswith("boys bantam "):
        return "bantam"
    if name_normalized.startswith("boys - bantam "):
        return "bantam"
    if name_normalized.startswith("boys - bantams "):
        return "bantam"
    if name_normalized.startswith("rookie bantam "):
        return "bantam"
    if name_normalized.startswith("rookie boys bantam "):
        return "bantam"
    if name_normalized.startswith("open (bantam) "):
        return "bantam"
    if name_normalized.startswith("bantam(6,7,8) "):
        return "bantam"
    if name_normalized.startswith("8u "):
        return "bantam"
    if name_normalized.startswith("7&8 "):
        return "bantam"

    if name_normalized.startswith("intermediate "):
        return "intermediate"
    if name_normalized.startswith("intermediate-"):
        return "intermediate"
    if name_normalized.startswith("intermediate("):
        return "intermediate"
    if name_normalized.startswith("intermediate:"):
        return "intermediate"
    if name_normalized.startswith("boys intermediate "):
        return "intermediate"
    if name_normalized.startswith("boys - intermediate "):
        return "intermediate"
    if name_normalized.startswith("boys - intermediates "):
        return "intermediate"
    if name_normalized.startswith("rookie intermediate "):
        return "intermediate"
    if name_normalized.startswith("rookie boys intermediate "):
        return "intermediate"
    if name_normalized.startswith("rookie boys intermeidate "):
        return "intermediate"
    if name_normalized.startswith("open (intermediate) "):
        return "intermediate"
    if name_normalized.startswith("10u "):
        return "intermediate"
    if name_normalized.startswith("elite 10u "):
        return "intermediate"
    if name_normalized.startswith("9&10 "):
        return "intermediate"

    if name_normalized.startswith("novice "):
        return "novice"
    if name_normalized.startswith("novice("):
        return "novice"
    if name_normalized.startswith("novice-"):
        return "novice"
    if name_normalized.startswith("novice:"):
        return "novice"
    if name_normalized.startswith("boys novice "):
        return "novice"
    if name_normalized.startswith("boys - novice "):
        return "novice"
    if name_normalized.startswith("rookie boys novice "):
        return "novice"
    if name_normalized.startswith("open (novice) "):
        return "novice"
    if name_normalized.startswith("12u "):
        return "novice"
    if name_normalized.startswith("11&12 "):
        return "novice"

    if name_normalized.startswith("senior "):
        return "senior"
    if name_normalized.startswith("senior-"):
        return "senior"
    if name_normalized.startswith("senior("):
        return "senior"
    if name_normalized.startswith("senior:"):
        return "senior"
    if name_normalized.startswith("seniors "):
        return "senior"
    if name_normalized.startswith("boys senior "):
        return "senior"
    if name_normalized.startswith("boys - senior "):
        return "senior"
    if name_normalized.startswith("rookie boys senior "):
        return "senior"
    if name_normalized.startswith("open (senior) "):
        return "senior"
    if name_normalized.startswith("boys - nov & sen "):
        return "senior"
    if name_normalized.startswith("boys - seniors "):
        return "senior"
    if name_normalized.startswith("14u "):
        return "senior"
    if name_normalized.startswith("13&14 "):
        return "senior"
    if name_normalized.startswith("elite "):
        return "senior"

    return None
