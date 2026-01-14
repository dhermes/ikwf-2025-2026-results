import pathlib
from typing import Literal

import bs4
import pydantic

_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")


class _Athlete(_ForbidExtra):
    usaw_number: str
    name: str
    ikwf_age: int


_Sectional = Literal[
    "Central",
    "North",
    "South",
    "West",
    "Central Chicago",
    "North Chicago",
    "South Chicago",
    "West Chicago",
]


class _ClubInfo(_ForbidExtra):
    club_name: str
    sectional: _Sectional
    athletes: list[_Athlete]


class _Clubs(pydantic.RootModel[list[_ClubInfo]]):
    pass


def _parse_file(path: pathlib.Path) -> _ClubInfo:
    with open(path) as file_obj:
        html = file_obj.read()

    soup = bs4.BeautifulSoup(html, features="html.parser")

    club_divs = soup.find_all("div", id="club")
    if len(club_divs) != 1:
        raise NotImplementedError(path.name)

    club_div = club_divs[0]
    club_h1s = club_div.find_all("h1")
    if len(club_h1s) != 1:
        raise NotImplementedError(path.name)

    club_h1 = club_h1s[0]
    club_content = club_h1.text.strip()
    club_name, remaining = club_content.rsplit(" (", 1)
    if not remaining.endswith(")"):
        raise NotImplementedError(club_content)

    sectional = remaining[:-1]

    wrestler_divs = soup.find_all("div", id="wrestler")
    if len(wrestler_divs) != 1:
        raise NotImplementedError(path.name)

    wrestler_div = wrestler_divs[0]
    athletes: list[_Athlete] = []
    all_td = wrestler_div.find_all("td")
    for td in all_td:
        td_content = td.text.strip()
        if not td_content:
            continue

        usaw_number, remaining = td_content.split(" - ", 1)

        name, remaining = remaining.rsplit(" (", 1)
        if not remaining.endswith(")"):
            raise NotImplementedError(td_content)

        ikwf_age = int(remaining[:-1])
        athletes.append(_Athlete(usaw_number=usaw_number, name=name, ikwf_age=ikwf_age))

    return _ClubInfo(club_name=club_name, sectional=sectional, athletes=athletes)


def _sort_func(club_info: _ClubInfo) -> tuple[str, str]:
    return club_info.sectional, club_info.club_name


def main() -> None:
    rosters_directory = _ROOT / "_raw-data" / "ikwf-rosters"
    club_infos: list[_ClubInfo] = []
    for path in rosters_directory.glob("*.html"):
        club_info = _parse_file(path)
        club_infos.append(club_info)

    club_infos.sort(key=_sort_func)

    root = _Clubs(root=club_infos)
    as_json = root.model_dump_json(indent=2)
    rosters_file = _ROOT / "_parsed-data" / "rosters.json"
    with open(rosters_file, "w") as file_obj:
        file_obj.write(as_json)
        file_obj.write("\n")


if __name__ == "__main__":
    main()
