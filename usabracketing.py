import os
import time
from typing import Literal

import bs4
import pydantic
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import Select, WebDriverWait

import bracket_util

_WAIT_TIME = 3
_LONG_CONTENT_WAIT_TIME = 15
_ENV_USERNAME = "USA_BRACKETING_USERNAME"
_ENV_PASSWORD = "USA_BRACKETING_PASSWORD"
_OPTION_ILLINOIS_VALUE = "14"
_OPTION_ILLINOIS_TEXT = "Illinois, USA"
_P_STYLE_DIVISION = "margin-top: 10px; font-weight: bold;"
_P_STYLE_ROUND_OR_BRACKET = "margin-top: 5px; font-weight: bold;"
_PLACEHOLDER_TEXT = "[first_name] [last_name]"
# NOTE: USA Bracketing puts USAW national championship events in search results
#       even if they don't match the search criteria.
_IGNORE_SEARCH_RESULT = "2026 USA Wrestling Kids Folkstyle National Championship"

TOURNAMENT_EVENTS: tuple[tuple[str, str], ...] = (
    ("2025-12-07", "42nd Annual Bulls Wrestling Tournament"),
    ("2025-12-14", "CICC Classic"),
    ("2025-12-14", "Wilbur Borrero Classic"),
    ("2025-12-21", "2025 Rocket Blast"),
    ("2025-12-21", "Jr. Porter Invite"),
    ("2025-12-21", "Spartan Beginner Tournament"),
    ("2025-12-21", "Stillman Valley Holiday Tournament"),
    ("2025-12-28", "Granite City Kids Holiday Classic"),
    ("2025-12-30", "Rockford Bad Boys & Girls Open"),
    ("2026-01-10", "Stillman Valley Beginners Tournament"),
    ("2026-01-11", "Chauncey Carrick Good Guys Tournament"),
    ("2026-01-11", "Morton Youth Wrestling 2026"),
    ("2026-01-11", "Spartan 300"),
    ("2026-01-18", "Jon Davis Kids Open"),
    ("2026-01-25", "Big Cat Wrestling Tournament"),
    ("2026-01-25", "Spartan Rumble"),
)
DUAL_EVENTS: tuple[tuple[str, str], ...] = (
    ("2026-01-04", "IKWF Southern Dual Meet Divisional"),
)


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError("Missing required environment variable", name)
    return value


class LoginInfo(_ForbidExtra):
    username: str
    password: str


def get_login_info() -> LoginInfo:
    username = _require_env(_ENV_USERNAME)
    password = _require_env(_ENV_PASSWORD)
    return LoginInfo(username=username, password=password)


def _has_multiple_tabs(driver: webdriver.Chrome):
    return len(driver.window_handles) > 1


def _login_website(driver: webdriver.Chrome, login_info: LoginInfo) -> None:
    # wait until the `login` input is present and visible
    login_input = WebDriverWait(driver, _WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "login"))
    )
    # clear any existing text and type the username
    login_input.clear()
    time.sleep(0.05)
    login_input.send_keys(login_info.username)

    # wait until the `password` input is present and visible
    password_input = WebDriverWait(driver, _WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "password"))
    )

    # clear any existing text and type the username
    password_input.clear()
    time.sleep(0.05)
    password_input.send_keys(login_info.password)
    time.sleep(0.05)

    # Click the log in button
    login_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Log in']"))
    )

    login_button.click()


def _go_to_events(driver: webdriver.Chrome) -> None:
    # Wait until login completes (URL changes off the login page)
    WebDriverWait(driver, _WAIT_TIME).until(EC.url_contains("usabracketing.com"))

    # Now go where you want
    driver.get("https://www.usabracketing.com/events")


def _click_search_events(driver: webdriver.Chrome) -> None:
    xpath_query = "//button[@type='button' and normalize-space()='Search Events']"
    open_search_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath_query))
    )

    open_search_button.click()


def _fill_out_event_search(driver: webdriver.Chrome, event: bracket_util.Event) -> None:
    end_date = event.end_date
    start_date = event.start_date or end_date
    end_date_str = end_date.strftime("%m/%d/%Y")
    start_date_str = start_date.strftime("%m/%d/%Y")

    # Input: "Event Name"
    event_name = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "event_name"))
    )

    event_name.clear()
    time.sleep(0.05)
    event_name.send_keys(event.name)
    time.sleep(0.05)

    # Input: "State"
    state_select_outer = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "event_state_ids"))
    )
    state_select = Select(state_select_outer)
    state_select.deselect_all()
    state_select.select_by_value(_OPTION_ILLINOIS_VALUE)

    xpath_query = "//select[@id='event_state_ids']/option[@value='14']"
    select_option = driver.find_element(By.XPATH, xpath_query)
    select_option_text = select_option.text
    if select_option_text != _OPTION_ILLINOIS_TEXT:
        raise RuntimeError("Unexpected option value", select_option_text)

    # Input: "Event Dates"
    date_type_select_outer = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "date_type"))
    )
    date_type_select = Select(date_type_select_outer)
    date_type_select.select_by_value("all")

    # Input: "Start Date"
    start_date_input = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "event_start_date"))
    )
    start_date_input.clear()
    time.sleep(0.05)
    start_date_input.send_keys(start_date_str)
    time.sleep(0.05)

    # Input: "End Date"
    end_date_input = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "event_end_date"))
    )
    end_date_input.clear()
    time.sleep(0.05)
    end_date_input.send_keys(end_date_str)
    time.sleep(0.05)


def _click_search_events_in_form(driver: webdriver.Chrome) -> None:
    xpath_query = "//button[@type='submit' and normalize-space()='Search Events']"
    search_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath_query))
    )

    search_button.click()


def _search_results_click_first(driver: webdriver.Chrome, name: str) -> str:
    table_body = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.events tbody"))
    )
    all_trs = table_body.find_elements(By.TAG_NAME, "tr")

    tr = None
    if len(all_trs) == 1:
        tr = all_trs[0]
    elif len(all_trs) == 2:
        first_html = all_trs[0].get_attribute("outerHTML")
        if _IGNORE_SEARCH_RESULT in first_html:
            tr = all_trs[1]

    if tr is None:
        raise ValueError(f"Expected exactly 1 <tr>, found {len(all_trs)}", name)

    event_name_td = tr.find_element(By.CSS_SELECTOR, "td:nth-child(2) a.basic_link")
    event_name = event_name_td.text

    clickable_cell = tr.find_element(By.CSS_SELECTOR, "td.clickable")
    clickable_cell.click()

    return event_name


def _open_event(event: bracket_util.Event, login_info: LoginInfo) -> webdriver.Chrome:
    driver = webdriver.Chrome()
    driver.get("https://www.usabracketing.com/login")

    _login_website(driver, login_info)
    _go_to_events(driver)
    _click_search_events(driver)
    _fill_out_event_search(driver, event)
    _click_search_events_in_form(driver)
    event_name = _search_results_click_first(driver, event.name)
    if event_name != event.name:
        raise RuntimeError(
            "Tournament name does not agree with name on USA Bracketing",
            event.name,
            event_name,
        )

    return driver


def _click_results(driver: webdriver.Chrome) -> None:
    reports_link = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[.//div[contains(text(),'Reports')]]")
        )
    )

    reports_link.click()


def _choose_ap_bouts(driver: webdriver.Chrome) -> None:
    # Wait until the report <select> is clickable
    report_select_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "report"))
    )

    # Wrap it in Selenium's Select
    report_select = Select(report_select_element)

    # Select the option by value
    report_select.select_by_value("ap_bouts")


def _allow_all_wrestlers(driver: webdriver.Chrome) -> None:
    # Wait until the "My Wrestlers Only" <select> is clickable
    my_wrestlers_select_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "my_wrestlers"))
    )

    my_wrestlers_select = Select(my_wrestlers_select_element)

    # Select the option by value
    my_wrestlers_select.select_by_value("")


class _OptionInfo(_ForbidExtra):
    value: str
    label: str


def _all_round_option_values(driver: webdriver.Chrome) -> list[_OptionInfo]:
    select_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "round_ids"))
    )

    select = Select(select_element)

    options: list[_OptionInfo] = []
    for opt in select.options:
        options.append(
            _OptionInfo(value=opt.get_attribute("value"), label=opt.text.strip())
        )

    return options


def _capture_round_html(
    driver: webdriver.Chrome, option_info: _OptionInfo, original_window: str
) -> str | None:
    # Clear old rounds and pick round ID
    round_select_outer = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "round_ids"))
    )
    round_select = Select(round_select_outer)
    round_select.deselect_all()
    time.sleep(0.05)
    round_select.select_by_value(option_info.value)
    time.sleep(0.05)

    # Click "Submit"
    submit_xpath = "//button[normalize-space()='Submit']"
    submit_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, submit_xpath))
    )
    submit_button.click()

    # Wait until the new tab exists
    WebDriverWait(driver, _WAIT_TIME).until(_has_multiple_tabs)

    # Switch to the new tab
    new_handles = [
        handle for handle in driver.window_handles if handle != original_window
    ]
    (new_window,) = new_handles
    driver.switch_to.window(new_window)

    # Wait until content finishes loading
    WebDriverWait(driver, _LONG_CONTENT_WAIT_TIME).until(
        EC.url_contains("/printing/matches")
    )

    # Grab the full HTML for the bracket once loaded
    root_div_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > div[style='font-size:12pt;']")
        )
    )
    round_html = root_div_element.get_attribute("outerHTML")

    # Close the current tab
    driver.close()

    # Back to original tab
    driver.switch_to.window(original_window)

    return round_html


def fetch_tournament_rounds(
    event: bracket_util.Event, login_info: LoginInfo
) -> dict[str, str]:
    driver = _open_event(event, login_info)
    _click_results(driver)
    _choose_ap_bouts(driver)
    _allow_all_wrestlers(driver)
    all_rounds = _all_round_option_values(driver)

    original_window = driver.current_window_handle
    captured_html: dict[str, str] = {}
    for option in all_rounds:
        key = option.label
        if key in captured_html:
            raise KeyError("Duplicate key", key)

        html = _capture_round_html(driver, option, original_window)
        if html is not None:
            captured_html[key] = html

    driver.quit()

    return captured_html


def _choose_weight_result_bouts(driver: webdriver.Chrome) -> None:
    # Wait until the report <select> is clickable
    report_select_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "report"))
    )

    # Wrap it in Selenium's Select
    report_select = Select(report_select_element)

    # Select the option by value
    report_select.select_by_value("weight_results")


def _all_weight_option_values(driver: webdriver.Chrome) -> list[_OptionInfo]:
    select_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "weight_ids"))
    )

    select = Select(select_element)

    options: list[_OptionInfo] = []
    for opt in select.options:
        options.append(
            _OptionInfo(value=opt.get_attribute("value"), label=opt.text.strip())
        )

    return options


def _capture_weight_html(
    driver: webdriver.Chrome, option_info: _OptionInfo, original_window: str
) -> str | None:
    # Clear old weights and pick round ID
    weight_select_outer = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "weight_ids"))
    )
    weight_select = Select(weight_select_outer)
    weight_select.deselect_all()
    time.sleep(0.05)
    weight_select.select_by_value(option_info.value)
    time.sleep(0.05)

    # Click "Submit"
    submit_xpath = "//button[normalize-space()='Submit']"
    submit_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, submit_xpath))
    )
    submit_button.click()

    # Wait until the new tab exists
    WebDriverWait(driver, _WAIT_TIME).until(_has_multiple_tabs)

    # Switch to the new tab
    new_handles = [
        handle for handle in driver.window_handles if handle != original_window
    ]
    (new_window,) = new_handles
    driver.switch_to.window(new_window)

    # Wait until content finishes loading
    WebDriverWait(driver, _LONG_CONTENT_WAIT_TIME).until(
        EC.url_contains("/printing/duals")
    )

    # Grab the full HTML for the bracket once loaded
    root_div_element = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "body > div[style='font-size:12pt;']")
        )
    )
    weight_html = root_div_element.get_attribute("outerHTML")

    # Close the current tab
    driver.close()

    # Back to original tab
    driver.switch_to.window(original_window)

    return weight_html


def fetch_athlete_weights(
    event: bracket_util.Event, login_info: LoginInfo
) -> dict[str, str]:
    return {}


def fetch_dual_weights(
    event: bracket_util.Event, login_info: LoginInfo
) -> dict[str, str]:
    driver = _open_event(event, login_info)
    _click_results(driver)
    _choose_weight_result_bouts(driver)
    _allow_all_wrestlers(driver)
    all_weights = _all_weight_option_values(driver)

    original_window = driver.current_window_handle
    captured_html: dict[str, str] = {}
    for option in all_weights:
        key = option.label
        if key in captured_html:
            raise KeyError("Duplicate key", key)

        html = _capture_weight_html(driver, option, original_window)
        if html is not None:
            captured_html[key] = html

    driver.quit()

    return captured_html


_ElementType = Literal["division", "round", "bracket", "match"]


def _determine_division(division_text: str) -> bracket_util.Division | None:
    normalized_text = division_text.lower()

    if normalized_text == "girls":
        return None

    if normalized_text == "girls - tot":
        return "girls_tot"

    if normalized_text == "girls - bantam":
        return "girls_bantam"
    if normalized_text.startswith("girls bantam "):
        return "girls_bantam"
    if normalized_text == "bantam girls":
        return "girls_bantam"

    if normalized_text == "girls - intermediate":
        return "girls_intermediate"
    if normalized_text == "intermediate girls":
        return "girls_intermediate"
    if normalized_text.startswith("girls intermediate "):
        return "girls_intermediate"

    if normalized_text == "girls - novice":
        return "girls_novice"
    if normalized_text == "novice girls":
        return "girls_novice"
    if normalized_text.startswith("girls novice "):
        return "girls_novice"

    if normalized_text == "girls - senior":
        return "girls_senior"
    if normalized_text.startswith("girls senior "):
        return "girls_senior"
    if normalized_text == "senior girls":
        return "girls_senior"
    if normalized_text.startswith("senior girls "):
        return "girls_senior"

    ############################################################################

    if normalized_text in ("tot", "tots", "boys - tot", "tots 6 & under"):
        return "tot"
    if normalized_text.startswith("tot "):
        return "tot"

    if normalized_text in ("bantam", "boys - bantam", "bantam 6, 7 & 8", "open-bantam"):
        return "bantam"
    if normalized_text.startswith("boys bantam "):
        return "bantam"

    if normalized_text in (
        "intermediate",
        "boys - intermediate",
        "intermediate 8, 9 & 10",
        "open-intermediate",
        "elite-intermediate",
    ):
        return "intermediate"
    if normalized_text.startswith("boys intermediate "):
        return "intermediate"

    if normalized_text in (
        "novice",
        "boys - novice",
        "novice boys 10, 11 & 12",
        "open-novice",
        "elite-novice",
    ):
        return "novice"
    if normalized_text.startswith("boys novice "):
        return "novice"

    if normalized_text in (
        "senior",
        "boys - senior",
        "senior boys 12, 13 & 14",
        "open-senior",
        "elite-senior",
    ):
        return "senior"
    if normalized_text.startswith("boys senior "):
        return "senior"

    raise NotImplementedError(division_text)


def _determine_result_type(result: str) -> bracket_util.ResultType | None:
    if result.startswith("Disq. "):
        return None
    if result == "Disq.":
        return None

    if result == "Rule":
        return None

    if result.startswith("Inj. "):
        return None
    if result == "Inj.":
        return None

    if result == "Def.":
        return None

    if result == "WIN":
        return None

    if result.startswith("SV "):
        return "overtime"
    if result.startswith("TB "):
        return "overtime"
    if result.startswith("Ult. "):
        return "overtime"
    if result.startswith("F.-SV "):
        return "overtime"

    if result.startswith("Dec. "):
        return "decision"

    if result.startswith("Maj. "):
        return "major"

    if result.startswith("T.F. "):
        return "tech"

    if result.startswith("F. "):
        return "pin"
    if result == "F.":
        return "pin"

    breakpoint()
    raise NotImplementedError(result)


def _parse_match_line(
    event_name: str,
    event_date: str,
    division: str,
    round_: str,
    bracket: str,
    match_text: str,
) -> bracket_util.MatchV1 | None:
    if _PLACEHOLDER_TEXT in match_text:
        return None
    if "Med. For. " in match_text:
        return None

    winner_full, remaining = match_text.split(") ")
    result_abbreviation, remaining = remaining.split(" ", 1)
    if result_abbreviation in ("For.", "vs."):
        return None

    winner, winner_team = winner_full.split(" (", 1)
    loser_full, score_or_time = remaining.split("),")
    score_or_time = score_or_time.strip()
    result = f"{result_abbreviation} {score_or_time}"
    result = result.strip()
    loser, loser_team = loser_full.split(" (", 1)

    result_type = _determine_result_type(result)
    if result_type is None:
        return None

    bracket_full = f"{division} {bracket}"
    bracket_full = bracket_full.strip()
    return bracket_util.MatchV1(
        event_name=event_name,
        event_date=event_date,
        bracket=bracket_full,
        round_=round_,
        division=_determine_division(division),
        winner=winner,
        winner_team=winner_team,
        loser=loser,
        loser_team=loser_team,
        result=result,
        result_type=result_type,
        source="usabracketing",
    )


def parse_tournament_round(
    html: str, event_name: str, event_date: str
) -> list[bracket_util.MatchV1]:
    """Parse a round from a tournament on TrackWrestling.

    These will be of the form:

        <div style="font-size: 12pt">
          <p style="margin-top: 10px; font-weight: bold">Tots</p>
          <p style="margin-top: 5px; font-weight: bold">Round 1</p>
          <p style="margin-top: 10px; font-weight: bold">Bantam</p>
          <p style="margin-top: 5px; font-weight: bold">Round 1</p>
          <p style="margin-top: 5px; font-weight: bold">52B</p>
          <p>{MATCH1 ...}</p>
          <p>{MATCH2 ...}</p>
          ...
        </div>

    I.e. the element is **ALWAYS** a <p> and the previous element + inline CSS
    `style` is the only thing we can use to determine what type of element it
    is.
    """
    round_matches: list[bracket_util.MatchV1] = []

    soup = bs4.BeautifulSoup(html, features="html.parser")
    all_p = soup.find_all("p")

    division: str | None = None
    round_: str | None = None
    bracket: str | None = None
    previous_type: _ElementType | None = None
    for entry_p in all_p:
        style = entry_p.get("style")
        entry_text = entry_p.text.strip()

        if style == _P_STYLE_DIVISION:
            if previous_type not in (None, "match", "round"):
                raise RuntimeError("Unexpected style for division", entry_p)
            division = entry_text
            previous_type = "division"
            continue

        if style == _P_STYLE_ROUND_OR_BRACKET:
            if previous_type == "division":
                round_ = entry_text
                previous_type = "round"
                continue

            if previous_type in ("round", "match"):
                bracket = entry_text
                previous_type = "bracket"
                continue

            raise RuntimeError("Unexpected style for entry", entry_p, previous_type)

        if previous_type in ("match", "bracket"):
            if division is None or round_ is None or bracket is None:
                raise RuntimeError(
                    "Unexpected style for match",
                    entry_p,
                    previous_type,
                    division,
                    round_,
                    bracket,
                )

            previous_type = "match"
            match_ = _parse_match_line(
                event_name, event_date, division, round_, bracket, entry_text
            )
            if match_ is not None:
                round_matches.append(match_)
            continue

        raise RuntimeError("Unexpected element", entry_p, previous_type)

    return round_matches
