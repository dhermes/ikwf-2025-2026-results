import os
import time

import pydantic
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import Select, WebDriverWait

import bracket_util

_WAIT_TIME = 3
_BOUT_FORMAT = (
    "[boutType] :: [wFName] :: [wLName] :: [wTeam] :: [winType] :: "
    "[lFName] :: [lLName] :: [lTeam] :: [scoreSummary]"
)
_VERBOSE = "VERBOSE" in os.environ


class _ForbidExtra(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", populate_by_name=True)


def _debug(message: str) -> None:
    if not _VERBOSE:
        return

    print(message)


def _main_page_click_events_classic(driver: webdriver.Chrome) -> None:
    # Wait for the element to appear
    span_xpath = (
        "//span[.//span[contains(@class, 'mobileHidden') and "
        "contains(normalize-space(.), 'Events')]]"
    )
    event_span = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, span_xpath))
    )
    # Click the <span>Events</span>
    event_span.click()


def _events_page_search_events(driver: webdriver.Chrome) -> None:
    # Wait for the button to be clickable
    event_search_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "eventSearchButton"))
    )

    # Click the button
    event_search_button.click()


def _event_search_fill_inputs(
    driver: webdriver.Chrome, search_inputs: dict[str, str]
) -> None:
    base_wait = WebDriverWait(driver, _WAIT_TIME)

    for field_id, value in search_inputs.items():
        input_element = base_wait.until(
            EC.presence_of_element_located((By.ID, field_id))
        )  # Wait for input to appear
        input_element.clear()  # Clear any existing text (if needed)
        input_element.send_keys(value)  # Enter the value


def _event_search_click_search(driver: webdriver.Chrome) -> None:
    # Wait for the button to be clickable
    search_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@value='Search']"))
    )

    # Click the button
    search_button.click()


def _search_results_click_first(driver: webdriver.Chrome, name: str) -> str:
    tournament_ul = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ul.tournament-ul"))
    )

    all_lis = tournament_ul.find_elements(By.XPATH, "./li")

    if len(all_lis) != 1:
        raise ValueError(f"Expected exactly 1 <li>, found {len(all_lis)}", name)

    li = all_lis[0]
    event_name_span = li.find_element(
        By.XPATH, ".//a[contains(@class,'segment-track')]/span[1]"
    )
    event_name = event_name_span.text.strip()

    anchor_link = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "anchor_0"))
    )

    anchor_link.click()

    return event_name


def _event_box_change_user_type(driver: webdriver.Chrome) -> None:
    # Wait for the "User Type" <select> to be clickable
    select_elem = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "userType"))
    )

    # Select the option we want `Viewer (classic)`
    Select(select_elem).select_by_visible_text("Viewer (classic)")


def _event_box_click_enter_event(driver: webdriver.Chrome) -> None:
    # Wait for the button to be clickable
    enter_event_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@value='Enter Event']"))
    )

    # Click the button
    enter_event_button.click()


def _click_results_sidebar_option(driver: webdriver.Chrome) -> None:
    # Wait for the iframe to be available
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )

    # Switch to the iframe
    driver.switch_to.frame(iframe)

    # Wait for the button to be clickable
    results_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "nav-results-button"))
    )

    # Click the button
    results_button.click()

    # Switch back to the main page
    driver.switch_to.default_content()


def _click_round_results_option(driver: webdriver.Chrome) -> None:
    # Wait for the iframe to be available
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )

    # Switch to the iframe
    driver.switch_to.frame(iframe)

    # Wait for the button to be clickable
    round_results = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Round Results"))
    )
    # Click the button
    round_results.click()

    # Switch back to the main page
    driver.switch_to.default_content()


class _OptionInfo(_ForbidExtra):
    value: str
    label: str


def _all_round_option_values(driver: webdriver.Chrome) -> list[_OptionInfo]:
    # Wait for the iframe to be available
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )

    # Switch to the iframe
    driver.switch_to.frame(iframe)

    select_elem = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "roundIdBox"))
    )

    select = Select(select_elem)

    options: list[_OptionInfo] = []
    for opt in select.options:
        options.append(
            _OptionInfo(value=opt.get_attribute("value"), label=opt.text.strip())
        )

    # Switch back to the main page
    driver.switch_to.default_content()

    return options


def _capture_round_html(
    driver: webdriver.Chrome, option_info: _OptionInfo
) -> str | None:
    # Wait for the iframe to be available
    _debug(":: Switching to <iframe>")
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )
    driver.switch_to.frame(iframe)
    time.sleep(0.05)

    # Update <select> for desired option
    _debug(f":: Changing <option>; {option_info.value!r}")
    xpath_query = f"//option[@value='{option_info.value}']"
    option = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath_query))
    )
    option.click()

    # Click "Advanced" so we can change the format
    _debug(':: Clicking "Advanced"')
    advanced_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".openExtraContent a"))
    )
    advanced_button.click()

    # Fill out the Format `<input>`
    _debug(':: Filling out "Advanced" format')
    format_input = WebDriverWait(driver, _WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "format"))
    )
    format_input.clear()
    time.sleep(0.05)
    format_input.send_keys(_BOUT_FORMAT)
    time.sleep(0.05)

    # Click "Go"
    _debug(':: Clicking "Go"')
    go_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//input[@type='button' and @value='Go']")
        )
    )
    go_button.click()
    time.sleep(0.05)

    # Wait for the "Filter" button to finish loading
    _debug(":: Waiting for round to load")
    filter_button = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "pageFunc_0"))
    )

    # Find the element we intend to capture `<section class="tw-list">`
    _debug(":: Capturing HTML")
    tw_lists = driver.find_elements(By.CSS_SELECTOR, "section.tw-list")
    if len(tw_lists) == 0:
        tw_list_html = None
    elif len(tw_lists) == 1:
        tw_list = tw_lists[0]
        # Get the outerHTML of the `<section class="tw-list">` element
        tw_list_html = tw_list.get_attribute("outerHTML")
    else:
        raise RuntimeError("Unexpected number of round results", option_info)

    # Click "Filter" to queue up searching for the next round, assumes the
    # button `id` is stable:
    # `<input type="button" id="pageFunc_0" value="Filter">`
    _debug(':: Clicking "Filter" to go back to search')
    filter_button.click()

    # Switch back to the main page (if needed)
    driver.switch_to.default_content()

    return tw_list_html


def _open_tournament(tournament: bracket_util.Tournament) -> webdriver.Chrome:
    end_date = tournament.end_date
    start_date = tournament.start_date or end_date
    search_inputs = {
        "nameBox": tournament.name,
        "startDateMonth": f"{start_date.month:02}",
        "startDateDay": f"{start_date.day:02}",
        "startDateYear": str(start_date.year),
        "endDateMonth": f"{end_date.month:02}",
        "endDateDay": f"{end_date.day:02}",
        "endDateYear": str(end_date.year),
    }

    driver = webdriver.Chrome()
    driver.get("https://www.trackwrestling.com/")

    _main_page_click_events_classic(driver)
    _events_page_search_events(driver)
    _event_search_fill_inputs(driver, search_inputs)
    _event_search_click_search(driver)
    event_name = _search_results_click_first(driver, tournament.name)
    if event_name != tournament.name:
        raise RuntimeError(
            "Tournament name does not agree with name on TrackWrestling",
            tournament.name,
            event_name,
        )

    _event_box_change_user_type(driver)
    _event_box_click_enter_event(driver)

    return driver


def fetch_tournament_rounds(tournament: bracket_util.Tournament) -> dict[str, str]:
    driver = _open_tournament(tournament)
    _click_results_sidebar_option(driver)
    _click_round_results_option(driver)
    all_rounds = _all_round_option_values(driver)

    captured_html: dict[str, str] = {}
    for option in all_rounds:
        if option.value == "" and option.label == "All Rounds":
            continue

        key = option.label
        if key in captured_html:
            raise KeyError("Duplicate key", key)

        html = _capture_round_html(driver, option)
        if html is not None:
            captured_html[key] = html

    driver.quit()

    return captured_html


def _click_weight_results_option(driver: webdriver.Chrome) -> None:
    # Wait for the iframe to be available
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )

    # Switch to the iframe
    driver.switch_to.frame(iframe)

    # Wait for the button to be clickable
    weight_results = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Weight Results"))
    )
    # Click the button
    weight_results.click()

    # Switch back to the main page
    driver.switch_to.default_content()


def _all_weight_option_values(driver: webdriver.Chrome) -> list[_OptionInfo]:
    # Wait for the iframe to be available
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )

    # Switch to the iframe
    driver.switch_to.frame(iframe)

    select_elem = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "groupBox"))
    )

    select = Select(select_elem)

    options: list[_OptionInfo] = []
    for opt in select.options:
        options.append(
            _OptionInfo(value=opt.get_attribute("value"), label=opt.text.strip())
        )

    # Switch back to the main page
    driver.switch_to.default_content()

    return options


def _capture_weight_html(
    driver: webdriver.Chrome, option_info: _OptionInfo
) -> str | None:
    # Wait for the iframe to be available
    _debug(":: Switching to <iframe>")
    iframe = WebDriverWait(driver, _WAIT_TIME).until(
        EC.presence_of_element_located((By.ID, "PageFrame"))
    )
    driver.switch_to.frame(iframe)
    time.sleep(0.05)

    # Update <select> for desired option
    _debug(f":: Changing <option>; {option_info.value!r}")
    xpath_query = f"//option[@value='{option_info.value}']"
    option = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.XPATH, xpath_query))
    )
    option.click()

    # Wait until <h1>{weight} results<h1> is visible
    results_text = f"{option_info.label} Results"
    WebDriverWait(driver, _WAIT_TIME).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "h1"), results_text)
    )

    # Find the element we intend to capture `<section class="tw-list">`
    _debug(":: Capturing HTML")
    tw_lists = driver.find_elements(By.CSS_SELECTOR, "section.tw-list")
    if len(tw_lists) == 0:
        tw_list_html = None
    elif len(tw_lists) == 1:
        tw_list = tw_lists[0]
        # Get the outerHTML of the `<section class="tw-list">` element
        tw_list_html = tw_list.get_attribute("outerHTML")
    else:
        raise RuntimeError("Unexpected number of weight results", option_info)

    # Switch back to the main page (if needed)
    driver.switch_to.default_content()

    return tw_list_html


def fetch_dual_weights(tournament: bracket_util.Tournament) -> dict[str, str]:
    driver = _open_tournament(tournament)
    _click_results_sidebar_option(driver)
    _click_weight_results_option(driver)
    all_weights = _all_weight_option_values(driver)

    captured_html: dict[str, str] = {}
    for option in all_weights:
        if option.value == "" and option.label == "":
            continue

        key = option.label
        if key in captured_html:
            raise KeyError("Duplicate key", key)

        html = _capture_weight_html(driver, option)
        if html is not None:
            captured_html[key] = html

    driver.quit()

    return captured_html
