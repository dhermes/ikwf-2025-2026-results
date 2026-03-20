import datetime
import pathlib
from typing import Literal

import pydantic

import bracket_util
import projection

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_EXPECTED_PLACES = ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th")
_IGNORED_EVENTS = (
    "IKWF Central Chicago Regional-Chicago",
    "IKWF Central Chicago Regional-Oak Lawn",
    "IKWF North Chicago Regional-Chicago",
    "IKWF South Chicago Regional-Joliet",
    "IKWF South Chicago Regional-Wilmington",
    "IKWF South Regional-Bethalto",
    "IKWF South Regional-Edwardsville",
    "IKWF South Regional-Mt. Vernon",
    "IKWF Central Regional-Mattoon",
    "IKWF Central Regional-Monticello",
    "IKWF North Chicago Regional-Antioch",
    "IKWF North Chicago Regional-Des Plaines",
    "IKWF North Regional-Algonquin",
    "IKWF North Regional-Byron",
    "IKWF West Chicago Regional-Villa Park",
    "IKWF West Chicago Regional-Wheaton",
    "IKWF West Regional-LaSalle",
    "IKWF West Regional-Macomb",
    "IKWF West Regional-Morton",
    ############################################################################
    "IKWF Central Chicago Sectional",
    "IKWF Central Sectional",
    "IKWF North Chicago Sectional",
    "IKWF North Sectional",
    "IKWF South Chicago Sectional",
    "IKWF South Sectional",
    "IKWF West Chicago Sectional",
    "IKWF West Sectional",
    ############################################################################
    "IKWF State Championships",
    ############################################################################
    "2026 Girls Rule Rumble",
    "2026 IL Kids Future Finalist",
    "IKWF Dual Meet State Championships",
    "Joe Tholl Sr. ELITE/OPEN 2025",
    "Jon Davis Kids Open",
    "THE Midwest Classic 2026",
)


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


class _StateQualifier(_ForbidExtra):
    division: bracket_util.Division
    weight: int
    name: str
    club: str
    placement_sectional: str
    sectional: _Sectional
    usaw_number: str
    placement_state: str


class _StateQualifiers(pydantic.RootModel[list[_StateQualifier]]):
    pass


def _load_qualifiers() -> list[_StateQualifier]:
    with open(_ROOT / "_parsed-data" / "2026-finalized.json", "rb") as file_obj:
        as_json = file_obj.read()

    extracted = _StateQualifiers.model_validate_json(as_json)
    return extracted.root


class _WinLoss(_ForbidExtra):
    wins: int
    losses: int

    def grade(self) -> int | None:
        matches = self.wins + self.losses
        if matches < 10:
            return None

        if self.wins < self.losses:
            return 0

        if self.wins < 3 * self.losses:
            return 1

        return 2


def _update_win_loss(
    usaw_number: str, all_records: dict[str, _WinLoss], win: bool
) -> None:
    if usaw_number not in all_records:
        all_records[usaw_number] = _WinLoss(wins=0, losses=0)

    win_loss = all_records[usaw_number]
    if win:
        win_loss.wins += 1
    else:
        win_loss.losses += 1

    all_records[usaw_number] = win_loss


def _bucket_matches(
    matches_v4: list[bracket_util.MatchV4],
) -> tuple[dict[str, set[str]], dict[str, _WinLoss]]:
    name_date_validation: dict[str, datetime.date] = {}
    mapped_usaw: dict[str, set[str]] = {}
    all_records: dict[str, _WinLoss] = {}
    for match_ in matches_v4:
        event_name = match_.event_name
        event_date = match_.event_date
        if event_name in name_date_validation:
            if name_date_validation[event_name] != event_date:
                raise ValueError("Repeat tournament name", event_name, event_date)
        else:
            name_date_validation[event_name] = event_date

        mapped_usaw.setdefault(event_name, set())

        winner_usaw = match_.winner_usaw_number
        if winner_usaw is not None:
            _update_win_loss(winner_usaw, all_records, True)
            mapped_usaw[event_name].add(winner_usaw)

        loser_usaw = match_.loser_usaw_number
        if loser_usaw is not None:
            _update_win_loss(loser_usaw, all_records, False)
            mapped_usaw[event_name].add(loser_usaw)

    return mapped_usaw, all_records


class _TournamentCredentials(_ForbidExtra):
    event_name: str
    total_wins: int
    total_losses: int
    champs: int
    finalists: int
    placers: int
    qualifiers: int
    grade1_record: int
    grade2_record: int
    score: float
    score_rank: int

    def event_score(self) -> float:
        total_matches = self.total_wins + self.total_losses
        win_pct = self.total_wins / total_matches if total_matches else 0

        win_score = win_pct * 100

        elite_score = (
            self.champs * 10
            + self.finalists * 6
            + self.placers * 3
            + self.qualifiers * 1
        )

        depth_score = self.grade2_record * 2 + self.grade1_record

        return win_score + elite_score + depth_score


def _score_tournament(
    event_name: str,
    usaw_numbers: set[str],
    all_records: dict[str, _WinLoss],
    state_result_map: dict[str, _StateQualifier],
) -> _TournamentCredentials:
    total_wins = 0
    total_losses = 0
    champs = 0
    finalists = 0
    placers = 0
    qualifiers = 0
    grade1_record = 0
    grade2_record = 0

    for usaw_number in usaw_numbers:
        win_loss = all_records[usaw_number]
        total_wins += win_loss.wins
        total_losses += win_loss.losses

        grade = win_loss.grade()
        if grade == 1:
            grade1_record += 1
        if grade == 2:
            grade2_record += 2

        qualifier = state_result_map.get(usaw_number)
        if qualifier is None:
            continue

        qualifiers += 1
        placement = qualifier.placement_state
        if placement == "":
            continue

        if placement not in _EXPECTED_PLACES:
            raise ValueError("Unexpected placement", placement)

        placers += 1
        if placement == "1st":
            champs += 1
            finalists += 1
        elif placement == "2nd":
            finalists += 1

    credentials = _TournamentCredentials(
        event_name=event_name,
        total_wins=total_wins,
        total_losses=total_losses,
        champs=champs,
        finalists=finalists,
        placers=placers,
        qualifiers=qualifiers,
        grade1_record=grade1_record,
        grade2_record=grade2_record,
        score=0.0,
        score_rank=-1,
    )
    credentials.score = credentials.event_score()
    return credentials


def _sort_score(credential: _TournamentCredentials) -> tuple[float, str]:
    return -credential.event_score(), credential.event_name


def _sort_champs(credential: _TournamentCredentials) -> tuple[int, str]:
    return -credential.champs, credential.event_name


def _sort_finalists(credential: _TournamentCredentials) -> tuple[int, str]:
    return -credential.finalists, credential.event_name


def _sort_placers(credential: _TournamentCredentials) -> tuple[int, str]:
    return -credential.placers, credential.event_name


def _sort_qualifiers(credential: _TournamentCredentials) -> tuple[int, str]:
    return -credential.qualifiers, credential.event_name


def _sort_wins(credential: _TournamentCredentials) -> tuple[int, str]:
    return -credential.total_wins, credential.event_name


def main() -> None:
    qualifiers = _load_qualifiers()
    state_result_map: dict[str, _StateQualifier] = {}
    for qualifier in qualifiers:
        usaw_number = qualifier.usaw_number
        if usaw_number in state_result_map:
            raise KeyError("Duplicate USAW number", usaw_number)
        state_result_map[usaw_number] = qualifier

    matches_v4 = projection.load_matches_v4()
    mapped_usaw, all_records = _bucket_matches(matches_v4)

    credentials = [
        _score_tournament(event_name, usaw_numbers, all_records, state_result_map)
        for event_name, usaw_numbers in mapped_usaw.items()
    ]
    credentials = [
        credential
        for credential in credentials
        if credential.event_name not in _IGNORED_EVENTS
    ]

    credentials.sort(key=_sort_score)
    for i, credential in enumerate(credentials):
        credential.score_rank = i + 1

    print("## Events by score")
    print("")
    for i, credential in enumerate(credentials):
        print(f"- {i + 1}: {credential.event_name}: {credential.score:.2f}")

    print("")
    print("## Events with most champs")
    print("")
    credentials.sort(key=_sort_champs)
    for i, credential in enumerate(credentials[:20]):
        print(
            f"- {i + 1}: {credential.event_name}: {credential.champs} "
            f"({credential.score_rank}, {credential.score:.2f})"
        )

    print("")
    print("## Events with most finalists")
    print("")
    credentials.sort(key=_sort_finalists)
    for i, credential in enumerate(credentials[:20]):
        print(
            f"- {i + 1}: {credential.event_name}: {credential.finalists} "
            f"({credential.score_rank}, {credential.score:.2f})"
        )

    print("")
    print("## Events with most placers")
    print("")
    credentials.sort(key=_sort_placers)
    for i, credential in enumerate(credentials[:20]):
        print(
            f"- {i + 1}: {credential.event_name}: {credential.placers} "
            f"({credential.score_rank}, {credential.score:.2f})"
        )

    print("")
    print("## Events with most qualifiers")
    print("")
    credentials.sort(key=_sort_qualifiers)
    for i, credential in enumerate(credentials[:20]):
        print(
            f"- {i + 1}: {credential.event_name}: {credential.qualifiers} "
            f"({credential.score_rank}, {credential.score:.2f})"
        )

    print("")
    print("## Events with most wins")
    print("")
    credentials.sort(key=_sort_wins)
    for i, credential in enumerate(credentials[:20]):
        print(
            f"- {i + 1}: {credential.event_name}: {credential.total_wins} "
            f"({credential.score_rank}, {credential.score:.2f})"
        )


if __name__ == "__main__":
    main()
