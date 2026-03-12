import json
import pathlib

import bs4
import pydantic
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

import bracket_util
import usabracketing

_WAIT_TIME = 3
_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_EXPECTED_LENGTH = 65
_ENTRY_INDICES = (
    0,
    4,
    6,
    8,
    12,
    14,
    16,
    20,
    22,
    24,
    28,
    30,
    32,
    36,
    38,
    40,
    44,
    46,
    48,
    52,
    54,
    56,
    60,
    62,
)


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


class _CapturedBrackets(pydantic.RootModel[dict[str, str]]):
    pass


class _Entry(_ForbidExtra):
    name: str
    team: str


class _WeightClass(_ForbidExtra):
    division: bracket_util.Division
    weight: int
    entries: list[_Entry | None]


class _WeightClasses(pydantic.RootModel[list[_WeightClass]]):
    pass


def _click_brackets(driver: webdriver.Chrome) -> None:
    brackets_link = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[.//div[contains(text(),'Brackets')]]")
        )
    )

    brackets_link.click()


def _get_brackets_list(driver: webdriver.Chrome) -> list[str]:
    # e.g. https://www.usabracketing.com/events/{EVENT_ID}/brackets
    base_url = driver.current_url
    _, last_part = base_url.rsplit("/", 1)
    if last_part != "brackets":
        raise RuntimeError("Unexpected URL", base_url)

    links = driver.find_elements(By.CSS_SELECTOR, f'a[href^="{base_url}/"]')
    hrefs = [link.get_attribute("href") for link in links]
    return hrefs


def _get_bracket_html(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)

    # NOTE: The bracket name is in a unique element of the form
    #       <span class="font-gotham antialiased text-xl text-usa-red font-extrabold">
    WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "span.font-gotham.antialiased.text-xl.text-usa-red.font-extrabold",
            )
        )
    )

    html = driver.page_source
    return html


def _capture_html() -> dict[str, str]:
    filename = _ROOT / "_raw-data" / "bracket-parsing" / "state-brackets.json"
    if filename.exists():
        with open(filename, "rb") as file_obj:
            contents = file_obj.read()

        validated = _CapturedBrackets.model_validate_json(contents)
        return validated.root

    login_info = usabracketing.get_login_info()

    event = bracket_util.Event(
        name="IKWF State Championships",
        start_date="2026-03-13",
        end_date="2026-03-14",
    )
    print(f"Fetching brackets for: {event.name} ...")

    driver = usabracketing.open_event(event, login_info)
    _click_brackets(driver)
    bracket_hrefs = _get_brackets_list(driver)

    captured: dict[str, str] = {}
    for bracket_href in bracket_hrefs:
        if bracket_href in captured:
            raise RuntimeError("Duplicate URL", bracket_href)
        html = _get_bracket_html(driver, bracket_href)
        captured[bracket_href] = html

    driver.quit()

    filename = _ROOT / "_raw-data" / "bracket-parsing" / "state-brackets.json"
    with open(filename, "w") as file_obj:
        json.dump(captured, file_obj, indent=2, sort_keys=True)
        file_obj.write("\n")

    return captured


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


def _extract_athlete(td: bs4.Tag) -> tuple[str, str] | None:
    parts = list(td.stripped_strings)
    parts = [part for part in parts if part != "_"]
    if parts == ["Bye"]:
        return None

    if len(parts) == 4:
        first_name, last_name, team, bout_number = parts
        int(bout_number)  # Assert it is an integer
    elif len(parts) == 3:
        first_name, last_name, team = parts
    else:
        raise ValueError("Unexpected athlete <td>", len(parts), parts, td)

    name = f"{first_name} {last_name}"
    team = team.strip().lstrip("(").rstrip(")").strip()
    return name.strip(), team


def _extract_bracket(key: str, html: str) -> _WeightClass:
    soup = bs4.BeautifulSoup(html, features="html.parser")
    bracket_spans = soup.find_all(
        "span", class_="font-gotham antialiased text-xl text-usa-red font-extrabold"
    )
    if len(bracket_spans) != 2:
        raise RuntimeError("Failed to load bracket", len(bracket_spans), key)

    bracket_names = set(bracket_span.text for bracket_span in bracket_spans)
    if len(bracket_names) != 1:
        raise RuntimeError("Failed to load bracket", len(bracket_names), key)

    (bracket_name,) = list(bracket_names)
    division_str, weight_str = bracket_name.rsplit(None, 1)
    weight = int(weight_str)
    division = _reverse_division(division_str)

    (bracket_pages,) = soup.find_all("div", id="bracketPages")
    inner_divs = bracket_pages.find_all("div", recursive=False)
    if len(inner_divs) != 2:
        raise RuntimeError("Failed to bracket pages", len(inner_divs), key)

    championship_bouts, _ = inner_divs
    (bracket_table,) = championship_bouts.find_all("table", recursive=False)
    (bracket_tbody,) = bracket_table.find_all("tbody", recursive=False)
    table_rows = bracket_tbody.find_all("tr", attrs={"height": "13px"}, recursive=False)
    if len(table_rows) != _EXPECTED_LENGTH:
        raise ValueError("Unexpected rows", len(table_rows))

    entries: list[_Entry | None] = []
    for index in _ENTRY_INDICES:
        tr = table_rows[index]
        all_td = tr.find_all("td", recursive=False)
        if len(all_td) < 2:
            raise ValueError("Unexpected row", index, len(all_td))
        athlete_td = all_td[1]
        extracted = _extract_athlete(athlete_td)
        if extracted is not None:
            name, team = extracted
            entries.append(_Entry(name=name, team=team))
        else:
            entries.append(None)

    if len(entries) != 24:
        raise RuntimeError("Unexpected number of entries")

    weight_class = _WeightClass(division=division, weight=weight, entries=entries)
    return weight_class


def main() -> None:
    captured = _capture_html()
    weight_classes: list[_WeightClass] = []
    for key, html in captured.items():
        weight_class = _extract_bracket(key, html)
        weight_classes.append(weight_class)

    weight_classes_root = _WeightClasses(root=weight_classes)
    weight_classes_json = weight_classes_root.model_dump_json(indent=2)

    filename = _ROOT / "_raw-data" / "bracket-parsing" / "state-entries.json"
    with open(filename, "w") as file_obj:
        file_obj.write(weight_classes_json)


if __name__ == "__main__":
    main()
