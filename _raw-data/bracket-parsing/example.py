import pathlib

import bs4

_HERE = pathlib.Path(__file__).resolve().parent
_ENTRY_INDICES = (0, 4, 6, 8, 12, 14, 16, 20, 22, 24, 28, 30)
_EXPECTED_LENGTH = 52


def _extract_athlete(td: bs4.Tag) -> tuple[str, str]:
    parts = list(td.stripped_strings)
    parts = [part for part in parts if part != "_"]
    if len(parts) != 3:
        raise ValueError("Unexpected athleted <td>", len(parts), parts, td)

    first_name, last_name, team = parts
    name = f"{first_name} {last_name}"
    return name.strip(), team


def main() -> None:
    with open(_HERE / "example.html") as file_obj:
        html = file_obj.read()

    soup = bs4.BeautifulSoup(html, features="html.parser")
    (bracket_pages,) = soup.find_all("div", id="bracketPages")
    (inner,) = bracket_pages.find_all("div", recursive=False)
    (bracket_table,) = inner.find_all("table", recursive=False)
    (bracket_tbody,) = bracket_table.find_all("tbody", recursive=False)
    table_rows = bracket_tbody.find_all("tr", attrs={"height": "16px"}, recursive=False)
    if len(table_rows) != _EXPECTED_LENGTH:
        raise ValueError("Unexpected rows", len(table_rows))

    for index in _ENTRY_INDICES:
        tr = table_rows[index]
        all_td = tr.find_all("td", recursive=False)
        if len(all_td) < 2:
            raise ValueError("Unexpected row", index, len(all_td))
        athlete_td = all_td[1]
        name, team = _extract_athlete(athlete_td)
        print((name, team))


if __name__ == "__main__":
    main()
