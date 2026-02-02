import datetime
import re
from typing import Literal

import pydantic

CSV_FIELD_NAMES_V1 = (
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
CSV_FIELD_NAMES_V2 = (
    "Event Name",
    "Event Date",
    "Bracket",
    "Round",
    "Division",
    "Winner",
    "Winner Team (normalized)",
    "Winner Team",
    "Loser",
    "Loser Team (normalized)",
    "Loser Team",
    "Result",
    "Result Type",
    "Source",
)
CSV_FIELD_NAMES_V3 = (
    "Event Name",
    "Event Date",
    "Bracket",
    "Round",
    "Division",
    ###############################
    "Winner (normalized)",
    "Winner USAW Number",
    "Winner IKWF Age",
    "Winner Team (normalized)",
    "Winner",
    "Winner Team",
    ###############################
    "Loser (normalized)",
    "Loser USAW Number",
    "Loser IKWF Age",
    "Loser Team (normalized)",
    "Loser",
    "Loser Team",
    ###############################
    "Result",
    "Result Type",
    "Source",
)
CSV_FIELD_NAMES_V4 = (
    "Event Name",
    "Event Date",
    "Bracket",
    "Round",
    "Division",
    ###############################
    "Winner (normalized)",
    "Winner weight",
    "Winner USAW Number",
    "Winner IKWF Age",
    "Winner Team (normalized)",
    "Winner",
    "Winner Team",
    ###############################
    "Loser (normalized)",
    "Loser weight",
    "Loser USAW Number",
    "Loser IKWF Age",
    "Loser Team (normalized)",
    "Loser",
    "Loser Team",
    ###############################
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


class Event(_ForbidExtra):
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


class FetchedEvent(_ForbidExtra):
    name: str
    source: Source
    start_date: datetime.date | None
    end_date: datetime.date
    match_html: dict[str, str]
    weights_html: dict[str, str]


class MatchV1(_ForbidExtra):
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


class MatchesV1(pydantic.RootModel[list[MatchV1]]):
    pass


class MatchV2(MatchV1):
    winner_team_normalized: str = pydantic.Field(alias="Winner Team (normalized)")
    loser_team_normalized: str = pydantic.Field(alias="Loser Team (normalized)")

    @classmethod
    def from_v1(
        cls, inherit: MatchV1, winner_team_normalized: str, loser_team_normalized: str
    ) -> MatchV2:
        data = inherit.model_dump(mode="json")
        data["winner_team_normalized"] = winner_team_normalized
        data["loser_team_normalized"] = loser_team_normalized
        return cls(**data)


class MatchesV2(pydantic.RootModel[list[MatchV2]]):
    pass


class MatchV3(MatchV2):
    winner_normalized: str | None = pydantic.Field(alias="Winner (normalized)")
    winner_usaw_number: str | None = pydantic.Field(alias="Winner USAW Number")
    winner_ikwf_age: int | None = pydantic.Field(alias="Winner IKWF Age")
    loser_normalized: str | None = pydantic.Field(alias="Loser (normalized)")
    loser_usaw_number: str | None = pydantic.Field(alias="Loser USAW Number")
    loser_ikwf_age: int | None = pydantic.Field(alias="Loser IKWF Age")

    @classmethod
    def from_v2(
        cls,
        inherit: MatchV2,
        winner_normalized: str | None,
        winner_usaw_number: str | None,
        winner_ikwf_age: int | None,
        loser_normalized: str | None,
        loser_usaw_number: str | None,
        loser_ikwf_age: int | None,
    ) -> MatchV3:
        data = inherit.model_dump(mode="json")
        data["winner_normalized"] = winner_normalized
        data["winner_usaw_number"] = winner_usaw_number
        data["winner_ikwf_age"] = winner_ikwf_age
        data["loser_normalized"] = loser_normalized
        data["loser_usaw_number"] = loser_usaw_number
        data["loser_ikwf_age"] = loser_ikwf_age
        return cls(**data)


class MatchesV3(pydantic.RootModel[list[MatchV3]]):
    pass


class MatchV4(MatchV3):
    winner_weight: float | None = pydantic.Field(alias="Winner weight")
    loser_weight: float | None = pydantic.Field(alias="Loser weight")

    @classmethod
    def from_v3(
        cls, inherit: MatchV3, winner_weight: float | None, loser_weight: float | None
    ) -> MatchV4:
        data = inherit.model_dump(mode="json")
        data["winner_weight"] = winner_weight
        data["loser_weight"] = loser_weight
        return cls(**data)


class MatchesV4(pydantic.RootModel[list[MatchV4]]):
    pass


def classify_bracket(name: str, event_name: str) -> Division | None:
    name_normalized = name.lower()

    if event_name == "Tots Bash":
        return "tot"

    if (
        name_normalized.startswith("open ")
        and event_name == "Joe Tholl Sr. ELITE/OPEN 2025"
    ):
        return "senior"

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
    if name_normalized.startswith("girls` bantam "):
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
    if name_normalized.startswith("girls` intermediate "):
        return "girls_intermediate"

    if name_normalized.startswith("girls novice "):
        return "girls_novice"
    if name_normalized.startswith("girls - novice "):
        return "girls_novice"
    if name_normalized.startswith("rookie girls novice "):
        return "girls_novice"
    if name_normalized.startswith("girls 12u "):
        return "girls_novice"
    if name_normalized.startswith("girls` novice "):
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
    if name_normalized.startswith("girls` senior "):
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

    if name_normalized.startswith("beginner bantam "):
        return "bantam"
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
    if name_normalized.startswith("bantam("):
        return "bantam"

    if name_normalized.startswith("beginner intermediate "):
        return "intermediate"
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
    if name_normalized.startswith("intermediates "):
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


AthleteWeightKey = tuple[str, str, str]


class AthleteWeight(_ForbidExtra):
    name: str
    group: str
    team: str
    weight: float | None

    def to_key(self) -> AthleteWeightKey:
        return self.name, self.group, self.team
