import csv
import pathlib

import bs4
import pydantic

import bracket_util
import club_util

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_WEIGHT_MARGIN_LEFT = "margin-left:0px"
_WRESTLER_MARGIN_LEFT = "margin-left:20px"
_EXPECTED_PLACES = ("1st", "2nd", "3rd", "4th", "5th", "6th")
_TEAM_REPLACE: dict[str, str] = {}
_CSV_COLUMNS = ("Division", "Weight", "Name", "Club", "USAW Number")


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class _SectionalQualifier(_ForbidExtra):
    division: bracket_util.Division = pydantic.Field(alias="Division")
    weight: int = pydantic.Field(alias="Weight")
    name: str = pydantic.Field(alias="Name")
    club: str = pydantic.Field(alias="Club")
    usaw_number: str | None = pydantic.Field(alias="USAW Number")


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
    if division == "senior" and weight == 174:
        # NOTE: Known issue in Oak Lawn
        return division, 164

    weights = bracket_util.weights_for_division(division)
    if weight not in weights:
        raise ValueError("Unexpected weight", div.text.strip())
    return division, weight


def _normalize_team(team: str) -> str:
    return _TEAM_REPLACE.get(team, team)


def _parse_wrestler_div(
    div: bs4.Tag,
    division_weight: tuple[bracket_util.Division, int],
    roster_map: dict[str, dict[str, club_util.Athlete]],
) -> _SectionalQualifier:
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
    athlete = athlete_map.get(name_key)
    if athlete is None:
        raise ValueError("Missing athlete", team_normalized, name)

    return _SectionalQualifier(
        division=division,
        weight=weight,
        name=athlete.name,
        club=team_normalized,
        usaw_number=athlete.usaw_number,
    )


def _add_qualifiers(
    path: pathlib.Path,
    qualifiers: list[_SectionalQualifier],
    roster_map: dict[str, dict[str, club_util.Athlete]],
) -> None:
    with open(path) as file_obj:
        html = file_obj.read()

    soup = bs4.BeautifulSoup(html, features="html.parser")
    (parent_div,) = soup.find_all("div", style="font-size:12pt;")
    direct_divs = parent_div.find_all("div", recursive=False)

    division_weight: tuple[bracket_util.Division, int] | None = None
    for div in direct_divs:
        margin_left = _get_margin_left_style(div)
        if margin_left == _WEIGHT_MARGIN_LEFT:
            division_weight = _parse_division_weight(div)
            continue

        if margin_left == _WRESTLER_MARGIN_LEFT:
            if division_weight is None:
                raise ValueError("Expected a division weight already", div)

            qualifiers.append(_parse_wrestler_div(div, division_weight, roster_map))
            continue

        raise RuntimeError("Unexpected margin", div)


def main() -> None:
    rosters = club_util.load_rosters()
    roster_map: dict[str, dict[str, club_util.Athlete]] = {}
    for roster in rosters:
        if roster.club_name in roster_map:
            raise KeyError("Duplicate team", roster.club_name)
        roster_map.setdefault(roster.club_name, {})
        for athlete in roster.athletes:
            name_key = athlete.name.lower()
            if name_key in roster_map[roster.club_name]:
                raise KeyError("Duplicate athlete", roster.club_name, name_key)

            roster_map[roster.club_name][name_key] = athlete

    qualifiers: list[_SectionalQualifier] = []

    placements_dir = _ROOT / "_raw-data" / "regional-final-placements"
    for path in placements_dir.glob("*.html"):
        _add_qualifiers(path, qualifiers, roster_map)

    qualifiers_filename = _ROOT / "_parsed-data" / "sectional-qualifiers.csv"
    with open(qualifiers_filename, "w") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        for qualifier in qualifiers:
            writer.writerow(qualifier.model_dump(mode="json", by_alias=True))


if __name__ == "__main__":
    main()
