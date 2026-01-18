import os
import time

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


def _fill_out_event_search(
    driver: webdriver.Chrome, tournament: bracket_util.Tournament
) -> None:
    end_date = tournament.end_date
    start_date = tournament.start_date or end_date
    end_date_str = end_date.strftime("%m/%d/%Y")
    start_date_str = start_date.strftime("%m/%d/%Y")

    # Input: "Event Name"
    event_name = WebDriverWait(driver, _WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "event_name"))
    )

    event_name.clear()
    time.sleep(0.05)
    event_name.send_keys(tournament.name)
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

    if len(all_trs) != 1:
        raise ValueError(f"Expected exactly 1 <tr>, found {len(all_trs)}", name)

    tr = all_trs[0]
    event_name_td = tr.find_element(By.CSS_SELECTOR, "td:nth-child(2) a.basic_link")
    event_name = event_name_td.text

    clickable_cell = tr.find_element(By.CSS_SELECTOR, "td.clickable")
    clickable_cell.click()

    return event_name


def _open_tournament(
    tournament: bracket_util.Tournament, login_info: LoginInfo
) -> webdriver.Chrome:
    driver = webdriver.Chrome()
    driver.get("https://www.usabracketing.com/login")

    _login_website(driver, login_info)
    _go_to_events(driver)
    _click_search_events(driver)
    _fill_out_event_search(driver, tournament)
    _click_search_events_in_form(driver)
    event_name = _search_results_click_first(driver, tournament.name)
    if event_name != tournament.name:
        raise RuntimeError(
            "Tournament name does not agree with name on USA Bracketing",
            tournament.name,
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
    tournament: bracket_util.Tournament, login_info: LoginInfo
) -> dict[str, str]:
    driver = _open_tournament(tournament, login_info)
    _click_results(driver)
    _choose_ap_bouts(driver)
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


def fetch_dual_weights(
    tournament: bracket_util.Tournament, login_info: LoginInfo
) -> dict[str, str]:
    driver = _open_tournament(tournament, login_info)
    _click_results(driver)
    _choose_weight_result_bouts(driver)
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
