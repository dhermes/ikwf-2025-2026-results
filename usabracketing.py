import os
import time
from collections.abc import Callable
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
_TITLE_MARGIN_LEFT = "margin-left:0px"
_WRESTLER_MARGIN_LEFT = "margin-left:20px"
_MATCH_MARGIN_LEFT = "margin-left:40px"
_ALLOWED_TEAM_EXTRA = (
    "IA",
    "IL - Male",
    "IL",
    "IN",
    "MO",
    "SC - Male",
    "SC",
    "VA",
    "WI",
)
_WEIGHTS_HEADERS1 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
    "Skill",
    "State",
)
_WEIGHTS_HEADERS2 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
    "Actual Weight",
)
_WEIGHTS_HEADERS3 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
    "Actual Weight",
    "Skill",
)
_WEIGHTS_HEADERS4 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
    "Skill",
)
_WEIGHTS_HEADERS5 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
    "Actual Weight",
    "Skill",
    "Grade",
)
_WEIGHTS_HEADERS6 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
    "Actual Weight",
    "State",
)
_WEIGHTS_HEADERS7 = (
    "First Name",
    "Last Name",
    "Team",
    "Divisions",
    "Weights",
)

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
    ("2026-02-01", "Cole Whitford Girls & Beginners Tournament"),
    ("2026-02-01", "Metamora Kids Wrestling Tournament"),
    ("2026-02-08", "Meet in the MIddle"),
    ("2026-02-22", "Champaign Grappler III"),
    ("2026-02-28", "IKWF Central Chicago Regional-Chicago"),
    ("2026-02-28", "IKWF Central Chicago Regional-Oak Lawn"),
    ("2026-02-28", "IKWF North Chicago Regional-Chicago"),
    ("2026-02-28", "IKWF South Chicago Regional-Joliet"),
    ("2026-02-28", "IKWF South Chicago Regional-Wilmington"),
    ("2026-02-28", "IKWF South Regional-Bethalto"),
    ("2026-02-28", "IKWF South Regional-Edwardsville"),
    ("2026-02-28", "IKWF South Regional-Mt. Vernon"),
    ("2026-03-01", "IKWF Central Regional-Mattoon"),
    ("2026-03-01", "IKWF Central Regional-Monticello"),
    ("2026-03-01", "IKWF North Chicago Regional-Antioch"),
    ("2026-03-01", "IKWF North Chicago Regional-Des Plaines"),
    ("2026-03-01", "IKWF North Regional-Algonquin"),
    ("2026-03-01", "IKWF North Regional-Byron"),
    ("2026-03-01", "IKWF West Chicago Regional-Villa Park"),
    ("2026-03-01", "IKWF West Chicago Regional-Wheaton"),
    ("2026-03-01", "IKWF West Regional-LaSalle"),
    ("2026-03-01", "IKWF West Regional-Macomb"),
    ("2026-03-01", "IKWF West Regional-Morton"),
)
DUAL_EVENTS: tuple[tuple[str, str], ...] = (
    ("2026-01-04", "IKWF Southern Dual Meet Divisional"),
    ("2026-02-01", "IKWF Dual Meet State Championships"),
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
    time.sleep(0.5)
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


def _allow_all_predicate(driver: webdriver.Chrome) -> None:
    all_my_wrestlers = driver.find_elements(By.ID, "my_wrestlers")
    all_my_teams = driver.find_elements(By.ID, "my_teams")

    my_wrestlers = None
    if len(all_my_wrestlers) > 1:
        raise RuntimeError("Unexpected `my_wrestlers` count")
    elif len(all_my_wrestlers) == 1:
        my_wrestlers = all_my_wrestlers[0]

    my_teams = None
    if len(all_my_teams) > 1:
        raise RuntimeError("Unexpected `my_teams` count")
    elif len(all_my_teams) == 1:
        my_teams = all_my_teams[0]

    if my_teams is not None and my_wrestlers is not None:
        raise RuntimeError("Unexpected both `my_teams` and `my_wrestlers` present")

    return my_teams or my_wrestlers


def _allow_all(driver: webdriver.Chrome) -> None:
    # Wait until the "My Wrestlers Only" or "My Teams Only" <select> is clickable
    my_only_select_element = WebDriverWait(driver, _WAIT_TIME).until(
        _allow_all_predicate
    )

    my_only_select = Select(my_only_select_element)

    # Select the option by value
    my_only_select.select_by_value("")


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
    _allow_all(driver)
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


def _navigate_to_wrestlers(driver: webdriver.Chrome) -> None:
    url = driver.current_url
    wrestlers_url = f"{url}/wrestlers"
    driver.get(wrestlers_url)


def _show_100_per_page(driver: webdriver.Chrome) -> None:
    select_elem = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'select[wire\\:model\\.live="perPage"]')
        )
    )
    select = Select(select_elem)
    select.select_by_value("100")
    time.sleep(2.0)


def _capture_wrestlers_table(driver: webdriver.Chrome) -> str:
    tables = driver.find_elements(By.TAG_NAME, "table")
    if len(tables) != 1:
        raise RuntimeError("Unexpected page layout, table count", len(tables))

    table = tables[0]
    html = table.get_attribute("outerHTML")
    time.sleep(2.0)
    return html


def _make_weights_next_page_ready(
    range_start: int,
) -> Callable[[webdriver.Chrome], str | None]:
    """Find the "Showing 26 to 50" text and wait for our page to load.

    <p class="text-sm text-gray-700 leading-5 mr-2">
      <span>Showing</span>
      <span class="font-medium">1</span>
      <span>to</span>
      <span class="font-medium">25</span>
    </p>
    """
    start_str = f"{range_start}"
    xpath_query = "//span[normalize-space(.)='Showing']/following-sibling::span[1]"

    def _weights_next_page_ready(driver: webdriver.Chrome) -> str | None:
        span = driver.find_element(By.XPATH, xpath_query)
        if span is None:
            return None

        text = span.text.strip()
        return text if text == start_str else None

    return _weights_next_page_ready


def _weights_click_next_page(driver: webdriver.Chrome, page_number: int) -> bool:
    range_start = 100 * page_number + 1

    buttons = driver.find_elements(By.CSS_SELECTOR, 'button[rel="next"]')

    if len(buttons) not in (0, 2):
        raise RuntimeError("Unexpected number of next buttons", len(buttons))

    next_page_exists = len(buttons) == 2
    if next_page_exists:
        button = buttons[0]
        button.click()
        predicate = _make_weights_next_page_ready(range_start)
        WebDriverWait(driver, _WAIT_TIME).until(predicate)
        time.sleep(0.5)

    return next_page_exists


def fetch_athlete_weights(
    event: bracket_util.Event, login_info: LoginInfo
) -> dict[str, str]:
    driver = _open_event(event, login_info)
    _navigate_to_wrestlers(driver)
    _show_100_per_page(driver)

    captured_html: dict[str, str] = {}

    next_page_exists = True
    # NOTE: This is a bounded `for` loop instead of a `while` loop.
    for i in range(10000):
        if not next_page_exists:
            break

        time.sleep(5.0)
        html = _capture_wrestlers_table(driver)
        key = f"page-{i}"
        captured_html[key] = html

        next_page_exists = _weights_click_next_page(driver, i)

    if next_page_exists:
        raise RuntimeError("Exited loop without terminating")

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


def fetch_dual_weights(
    event: bracket_util.Event, login_info: LoginInfo
) -> dict[str, str]:
    driver = _open_event(event, login_info)
    _click_results(driver)
    _choose_weight_result_bouts(driver)
    _allow_all(driver)
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

    if normalized_text in ("girls - tot", "girls tots", "g-tots"):
        return "girls_tot"

    if normalized_text in (
        "girls - bantam",
        "girls bantam",
        "g-bantam",
        "bantam girls",
        "girls 9u",
    ):
        return "girls_bantam"
    if normalized_text.startswith("girls bantam "):
        return "girls_bantam"

    if normalized_text in (
        "girls - intermediate",
        "girls intermediate",
        "g-intermediate",
        "intermediate girls",
    ):
        return "girls_intermediate"
    if normalized_text.startswith("girls intermediate "):
        return "girls_intermediate"

    if normalized_text in (
        "girls - novice",
        "girls novice",
        "g-novice",
        "novice girls",
    ):
        return "girls_novice"
    if normalized_text.startswith("girls novice "):
        return "girls_novice"

    if normalized_text in (
        "girls - senior",
        "girls senior",
        "g-senior",
        "senior girls",
    ):
        return "girls_senior"
    if normalized_text.startswith("girls senior "):
        return "girls_senior"
    if normalized_text.startswith("senior girls "):
        return "girls_senior"

    ############################################################################

    if normalized_text in ("tot", "tots", "boys - tot", "boys tots", "tots 6 & under"):
        return "tot"
    if normalized_text.startswith("tot "):
        return "tot"

    if normalized_text in (
        "bantam",
        "boys - bantam",
        "boys bantam",
        "bantam 6, 7 & 8",
        "open-bantam",
    ):
        return "bantam"
    if normalized_text.startswith("boys bantam "):
        return "bantam"

    if normalized_text in (
        "intermediate",
        "boys - intermediate",
        "boys intermediate",
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
        "boys novice",
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
        "boys senior",
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
    if result.startswith("ID "):
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
    if result.startswith("Dec "):
        return "decision"

    if result.startswith("Maj. "):
        return "major"
    if result.startswith("MD "):
        return "major"

    if result.startswith("T.F. "):
        return "tech"
    if result.startswith("TF "):
        return "tech"

    if result.startswith("F. "):
        return "pin"
    if result == "F.":
        return "pin"
    if result.startswith("F "):
        return "pin"

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

    has_cj = False
    if "Charles (CJ) " in match_text:
        has_cj = True
        match_text = match_text.replace("Charles (CJ) ", "Charles ")
    winner_full, remaining = match_text.split(") ")

    if remaining.startswith("Ult. Tie Br. "):
        result_abbreviation = "Ult. Tie Br."
        remaining = remaining[13:]
    else:
        result_abbreviation, remaining = remaining.split(" ", 1)

    if result_abbreviation in ("For.", "vs."):
        return None

    winner, winner_team = winner_full.split(" (", 1)
    loser_full, score_or_time = remaining.split("),")
    score_or_time = score_or_time.strip()
    result = f"{result_abbreviation} {score_or_time}"
    result = result.strip()
    loser, loser_team = loser_full.split(" (", 1)
    if has_cj:
        loser = loser.replace("Charles ", "Charles (CJ) ")

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


def _get_margin_left_style(tag: bs4.Tag) -> str:
    style = tag.get("style", "")
    matches = [part for part in style.split(";") if part.startswith("margin-left:")]
    if len(matches) != 1:
        raise RuntimeError("Unexpected tag style", style)

    return matches[0]


class _ParsedWrestler(_ForbidExtra):
    name: str
    team: str
    team_acronym: str


def _parse_wrestler_heading(tag: bs4.Tag) -> _ParsedWrestler:
    as_text = tag.text.strip()
    before, _ = as_text.split(" (")
    name, team = before.rsplit(", ", 1)
    return _ParsedWrestler(name=name, team=team, team_acronym="")


_ParsedDualMatchKey = tuple[str, str, str, str, str]


class _ParsedDualMatch(_ForbidExtra):
    bracket: str
    winner: str
    winner_team: str | None
    winner_team_acronym: str
    loser: str
    loser_team: str | None
    loser_team_acronym: str
    result: str

    def to_key(self) -> _ParsedDualMatchKey:
        return (
            self.bracket,
            self.winner,
            self.winner_team_acronym,
            self.loser,
            self.loser_team_acronym,
        )


def _parse_dual_match_line(
    wrestler: _ParsedWrestler, tag: bs4.Tag
) -> _ParsedDualMatch | None:
    nodes = list(tag.children)
    if len(nodes) == 3:
        last_node = nodes[2].text.strip()
        if "over Forfeit" not in last_node:
            raise ValueError("Unexpected forfeit tag", tag)
        return None

    if len(nodes) == 5:
        node0, node1, node2, node3, node4 = nodes

        bracket = node0.text.strip()
        if not bracket.endswith(" -"):
            raise ValueError("Unexpected bracket", bracket, tag)
        bracket = bracket[:-2]

        winner = node1.text.strip()

        winner_team_acronym = node2.text.strip()
        if not winner_team_acronym.startswith(", "):
            raise ValueError("Unexpected winner team", winner_team_acronym, tag)
        winner_team_acronym = winner_team_acronym[2:]
        if not winner_team_acronym.endswith(" over"):
            raise ValueError("Unexpected winner team", winner_team_acronym, tag)
        winner_team_acronym = winner_team_acronym[:-5]

        loser = node3.text.strip()

        loser_team_acronym, result = node4.text.strip().split(" (", 1)

        if not result.endswith(")"):
            raise ValueError("Unexpected result", result, tag)
        result = result[:-1]

        if not loser_team_acronym.startswith(", "):
            raise ValueError("Unexpected loser team", loser_team_acronym, tag)
        loser_team_acronym = loser_team_acronym[2:]

        if wrestler.name == loser:
            winner_team = None
            loser_team = wrestler.team
        elif wrestler.name == winner:
            winner_team = wrestler.team
            loser_team = None
        else:
            raise ValueError("Unexpected wrestler", wrestler.name, loser, winner)

        return _ParsedDualMatch(
            bracket=bracket,
            winner=winner,
            winner_team=winner_team,
            winner_team_acronym=winner_team_acronym,
            loser=loser,
            loser_team=loser_team,
            loser_team_acronym=loser_team_acronym,
            result=result,
        )

    raise ValueError("Unexpected match tag", tag)


def _extract_weight(key: str, html: str) -> list[_ParsedDualMatch]:
    soup = bs4.BeautifulSoup(html, features="html.parser")
    (parent_div,) = soup.find_all("div", style="font-size:12pt;")
    direct_divs = parent_div.find_all("div", recursive=False)

    current_wrestler: _ParsedWrestler | None = None
    parsed_matches: list[_ParsedDualMatch] = []
    for i, div in enumerate(direct_divs):
        margin_left = _get_margin_left_style(div)
        if margin_left == _TITLE_MARGIN_LEFT:
            if i != 0:
                raise RuntimeError("Unexpected title margin", div, i)
            if div.text.strip() != key:
                raise RuntimeError("Unexpected title", div, i)
            continue

        if margin_left == _WRESTLER_MARGIN_LEFT:
            current_wrestler = _parse_wrestler_heading(div)
            continue

        if margin_left == _MATCH_MARGIN_LEFT:
            if current_wrestler is None:
                raise RuntimeError("No current wrestler for a match", div, i)
            parsed_match = _parse_dual_match_line(current_wrestler, div)
            if parsed_match is not None:
                parsed_matches.append(parsed_match)
            continue

        raise RuntimeError("Unexpected margin", div, i)

    return parsed_matches


def _resolve_dual_matches(
    parsed_matches: list[_ParsedDualMatch],
) -> list[_ParsedDualMatch]:
    """Find the left and right side of a match to resolve team names."""
    with_team_resolved: list[_ParsedDualMatch] = []
    by_key: dict[_ParsedDualMatchKey, list[_ParsedDualMatch]] = {}

    for parsed_match in parsed_matches:
        key = parsed_match.to_key()
        by_key.setdefault(key, [])
        by_key[key].append(parsed_match)

    for key, matches in by_key.items():
        if len(matches) != 2:
            raise ValueError(
                "Unexpected number of matches for key", key, len(matches), matches
            )
        match1, match2 = matches
        if match1.winner_team is None:
            match1.winner_team = match2.winner_team
        if match1.loser_team is None:
            match1.loser_team = match2.loser_team

        if match1.winner_team is None or match1.loser_team is None:
            raise ValueError("Unexpected name resolution", match1, match2)

        with_team_resolved.append(match1)

    return with_team_resolved


def _division_for_event(event_name: str) -> bracket_util.Division:
    if event_name == "IKWF Southern Dual Meet Divisional":
        return "senior"
    if event_name == "IKWF Dual Meet State Championships":
        return "senior"

    raise NotImplementedError(event_name)


def parse_dual_event(
    weights_raw: dict[str, str], event_name: str, event_date: str
) -> list[bracket_util.MatchV1]:
    unresolved_team_matches: list[_ParsedDualMatch] = []
    for key, html in weights_raw.items():
        unresolved_team_matches.extend(_extract_weight(key, html))

    parsed_matches = _resolve_dual_matches(unresolved_team_matches)

    all_matches: list[bracket_util.MatchV1] = []
    for parsed_match in parsed_matches:
        result_type = _determine_result_type(parsed_match.result)
        if result_type is None:
            continue

        all_matches.append(
            bracket_util.MatchV1(
                event_name=event_name,
                event_date=event_date,
                bracket=parsed_match.bracket,
                round_="Dual",
                division=_division_for_event(event_name),
                winner=parsed_match.winner,
                winner_team=parsed_match.winner_team,
                loser=parsed_match.loser,
                loser_team=parsed_match.loser_team,
                result=parsed_match.result,
                result_type=result_type,
                source="usabracketing_dual",
            )
        )
    return all_matches


def _extract_wrestlers_columns1(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS1`"""
    first_name, last_name, team, _, group, _, _ = columns
    weight_str = ""
    return first_name, last_name, team, group, weight_str


def _extract_wrestlers_columns2(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS2`"""
    first_name, last_name, team, _, group, weight_str = columns
    return first_name, last_name, team, group, weight_str


def _extract_wrestlers_columns3(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS3`"""
    first_name, last_name, team, _, group, weight_str, _ = columns
    return first_name, last_name, team, group, weight_str


def _extract_wrestlers_columns4(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS4`"""
    first_name, last_name, team, _, group, _ = columns
    weight_str = ""
    return first_name, last_name, team, group, weight_str


def _extract_wrestlers_columns5(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS5`"""
    first_name, last_name, team, _, group, weight_str, _, _ = columns
    return first_name, last_name, team, group, weight_str


def _extract_wrestlers_columns6(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS6`"""
    first_name, last_name, team, _, group, weight_str, _ = columns
    return first_name, last_name, team, group, weight_str


def _extract_wrestlers_columns7(
    columns: tuple[str, ...],
) -> tuple[str, str, str, str, str]:
    """Extract values for `_WEIGHTS_HEADERS7`"""
    first_name, last_name, team, group, _ = columns
    weight_str = ""
    return first_name, last_name, team, group, weight_str


def _parse_weight_value(weight_str: str) -> float | None:
    if weight_str == "":
        return None

    return float(weight_str)


def _parse_team_full(team_full: str) -> str:
    parts = team_full.rsplit(", ", 1)
    if len(parts) == 1:
        return team_full

    team, extra = parts
    if extra not in _ALLOWED_TEAM_EXTRA:
        raise RuntimeError("Unexpected team line extra", extra, team_full)

    return team.strip()


def parse_athlete_weights(
    html: str,
) -> dict[bracket_util.AthleteWeightKey, bracket_util.AthleteWeight]:
    """Parse weights from "Wrestlers" page from an event on USA Bracketing."""
    all_weights: dict[bracket_util.AthleteWeightKey, bracket_util.AthleteWeight] = {}
    soup = bs4.BeautifulSoup(html, features="html.parser")

    (table,) = soup.find_all("table")
    rows = table.find_all("tr")

    all_th = rows[0].find_all("th")
    headers = tuple(
        th.find("span", class_="flex items-center").text.strip() for th in all_th
    )

    if headers == _WEIGHTS_HEADERS1:
        extract_func = _extract_wrestlers_columns1
    elif headers == _WEIGHTS_HEADERS2:
        extract_func = _extract_wrestlers_columns2
    elif headers == _WEIGHTS_HEADERS3:
        extract_func = _extract_wrestlers_columns3
    elif headers == _WEIGHTS_HEADERS4:
        extract_func = _extract_wrestlers_columns4
    elif headers == _WEIGHTS_HEADERS5:
        extract_func = _extract_wrestlers_columns5
    elif headers == _WEIGHTS_HEADERS6:
        extract_func = _extract_wrestlers_columns6
    elif headers == _WEIGHTS_HEADERS7:
        extract_func = _extract_wrestlers_columns7
    else:
        raise RuntimeError("Unexpected headers for table", headers)

    for row in rows[1:]:
        columns = tuple(
            td.text.strip().strip("\xa0").strip() for td in row.find_all("td")
        )
        first_name, last_name, team_full, group, weight_str = extract_func(columns)
        name = f"{first_name} {last_name}"
        weight = _parse_weight_value(weight_str)
        team = _parse_team_full(team_full)

        athlete_weight = bracket_util.AthleteWeight(
            name=name, group=group, team=team, weight=weight
        )
        key = athlete_weight.to_key()
        if key in all_weights:
            if all_weights[key] != athlete_weight:
                raise ValueError(
                    "Unexpected non-matching rows",
                    key,
                    athlete_weight,
                    all_weights[key],
                )
        else:
            all_weights[key] = athlete_weight

    return all_weights
