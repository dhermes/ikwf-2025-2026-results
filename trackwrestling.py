import os
import time

import bs4
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
_WIN_TYPE_MAP = {
    "won by decision over": "decision",
    "won by major decision over": "major",
    "won by tech fall over": "tech",
    "won by tech. fall over": "tech",
    "won by fall over": "pin",
    ###################################
    "won in sudden victory - 1 over": "overtime",
    "won in tie breaker - 1 over": "overtime",
    "won in overtime over": "overtime",
    "won in double overtime over": "overtime",
    "won in SV-1 by fall over": "overtime",
    "won in the ultimate tie breaker over": "overtime",
    "won in sudden victory - 2 over": "overtime",
    ###################################
    "received a bye": None,
    "won by forfeit over": None,
    "won by injury default over": None,
    "won by medical forfeit over": None,
    "won by disqualification over": None,
    "won by no contest over": None,
}
# NOTE: The following matches appeared in Dual match outputs but do not
#       include complete information, so they must be ignored.
_ERRONEOUS_DUAL_MATCHES = frozenset(
    [
        (
            "70 - Luke Bosack (Orland Park Pioneers (South Chicago)) over "
            "Eddie Gergits (Demolition (South Chicago))"
        ),
        (
            "90 - Gavin Garrity (Orland Park Pioneers (South Chicago)) over "
            "Aiden Samanich (Lemont Bears WC (Central Chicago))"
        ),
    ]
)
TOURNAMENT_EVENTS: tuple[tuple[str, str], ...] = (
    ("2025-12-06", "2025 EWC Beginners and Girls Tournament"),
    ("2025-12-06", "Tots Bash"),
    ("2025-12-07", "2025 Force Challenge 19"),
    ("2025-12-07", "2025 Mick Ruettiger Invitational"),
    ("2025-12-07", "2025 Oak Forest Green and White Tournament"),
    ("2025-12-07", "2025 Xtreme Challenge"),
    ("2025-12-07", "Capture the Eagle"),
    ("2025-12-07", "Elias George Memorial 2025"),
    ("2025-12-07", "Fox Lake Beginners Tournament"),
    ("2025-12-07", "Lawrence County Knights Terry Hoke Open"),
    ("2025-12-07", "Lil` Coalers Clash"),
    ("2025-12-07", "Lincoln Railer Rumble 2025"),
    ("2025-12-07", "Peoria Razorback Season Opener"),
    ("2025-12-07", "Tiger Takedown"),
    ("2025-12-13", "2025 O`Fallon Beginners/Girls Open"),
    ("2025-12-13", "Mattoon Beginners Tournament"),
    ("2025-12-13", "Roxana Rumble"),
    ("2025-12-14", "2025 Beat the Streets Youth Brawl"),
    ("2025-12-14", "2025 Orland Park Pioneer KickOff Classic"),
    ("2025-12-14", "ACES Rumble"),
    ("2025-12-14", "Countdown to Christmas DGWC"),
    ("2025-12-14", "December 2025 Lil Reapers Wrestling Classic"),
    ("2025-12-14", "John Nagy Throwdown 2025"),
    ("2025-12-14", "Rumble on the Red"),
    ("2025-12-20", "2025 Edwardsville Open"),
    ("2025-12-21", "2025 Mat Rat Invitational"),
    ("2025-12-21", "2025 Yeti Bash/Morris Kids WC"),
    ("2025-12-21", "309 Winter Classic"),
    ("2025-12-21", "Bulldog Brawl"),
    ("2025-12-21", "Clinton Challenge"),
    ("2025-12-21", "Cumberland Kids Open 2025"),
    ("2025-12-21", "Darby Pool Wrestling Tournament"),
    ("2025-12-21", "Highland Howl Jarron Haberer memorial"),
    ("2025-12-21", "Joe Tholl Sr. ELITE/OPEN 2025"),
    ("2025-12-27", "2025 Betty Martinez Memorial"),
    ("2025-12-27", "D/C Bolt New Years Bash"),
    ("2025-12-28", "2025 Naperville Reindeer Rumble"),
    ("2025-12-28", "2025 Dave Mattio Classic"),
    ("2025-12-28", "Crawford County Open"),
    ("2025-12-28", "2025 Sandwich WinterWonderSLAM"),
    ("2025-12-28", "Junior Midlands @ Northwestern University"),
    ("2025-12-31", "Cadet Classic"),
    ("2026-01-03", "2026 Boneyard Bash ELITE & ROOKIE"),
    ("2026-01-03", "2026 Hillsboro Jr. Topper Tournament"),
    ("2026-01-03", "Double D Demolition (SVWC Tournament)"),
    ("2026-01-04", "Oak Lawn Acorn Rookie Rumble"),
    ("2026-01-04", "THE Midwest Classic 2026"),
    ("2026-01-04", "Monticello Youth Open 2026"),
    ("2026-01-04", "The Little Giant Holiday Hammer"),
    ("2026-01-04", "Crushing Christmas Classic-Coal City"),
    ("2026-01-04", "2026 Bob Jahn Memorial"),
    ("2026-01-04", "Mattoon YWC - Bonic Battle for the Belt"),
    ("2026-01-10", "Hawk Wrestling Club Invitational"),
    ("2026-01-11", "Batavia Classic Wrestling Tournament"),
    ("2026-01-11", "2026CarbondaleDogFight&AlliRaganGirlsOpn"),
    ("2026-01-11", "2026 Coach Jim Craig Memorial-CLOSED"),
    ("2026-01-11", "Geneva Vikings Youth Tournament"),
    ("2026-01-11", "Devils Gauntlet Battle for the Belts"),
    ("2026-01-11", "Mt Zion kids club open"),
    ("2026-01-11", "Pontiac Kids Open 2026"),
    ("2026-01-11", "JAWS Battle in the Bowl"),
    ("2026-01-24", "2026 Girls Rule Rumble"),
    ("2026-01-25", "2026 Ezra Hill Jr Memorial Tournament"),
    ("2026-01-25", "2026 Susan Collins Memorial Tournament"),
    ("2026-01-25", "Cabin Fever 2026"),
    ("2026-01-25", "Celtic Open 2026"),
    ("2026-01-25", "DEMOLITION BATTLE OF RAGNAROK"),
    ("2026-01-25", "Geist Grappling Classic"),
    ("2026-01-25", "Harper Rookie Rumble"),
    ("2026-01-25", "LP Crunching Cavs Classic"),
    ("2026-01-25", "Pekin Custer/Stoudt Open"),
)
DUAL_EVENTS: tuple[tuple[str, str], ...] = (
    ("2025-12-14", "2025 Hub City Hammer Duals"),
    ("2026-01-10", "The Didi Duals 2026"),
)


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


def _open_event(event: bracket_util.Event) -> webdriver.Chrome:
    end_date = event.end_date
    start_date = event.start_date or end_date
    search_inputs = {
        "nameBox": event.name,
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
    event_name = _search_results_click_first(driver, event.name)
    if event_name != event.name:
        raise RuntimeError(
            "Event name does not agree with name on TrackWrestling",
            event.name,
            event_name,
        )

    _event_box_change_user_type(driver)
    _event_box_click_enter_event(driver)

    return driver


def fetch_tournament_rounds(event: bracket_util.Event) -> dict[str, str]:
    driver = _open_event(event)
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


def fetch_dual_weights(event: bracket_util.Event) -> dict[str, str]:
    driver = _open_event(event)
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


def parse_tournament_round(
    html: str, event_name: str, event_date: str
) -> list[bracket_util.MatchV1]:
    """Parse a round from a tournament on TrackWrestling.

    These will be of the form:

        <section class="tw-list">
          <h1>...</h1>
          <h2>{BRACKET NAME}</h2>
          <ul>
            <li>{MATCH 1 ...}</li>
            <li>{MATCH 2 ...}</li>
          </ul>
          ...
        </section>
    """
    round_matches: list[bracket_util.MatchV1] = []
    soup = bs4.BeautifulSoup(html, features="html.parser")

    all_h2 = soup.find_all("h2")
    all_ul = soup.find_all("ul")
    if len(all_h2) < len(all_ul):
        raise RuntimeError(
            "Unexpected HTML structure",
            event_name,
            len(all_h2),
            len(all_ul),
        )

    ul_count = 0
    for bracket_h2 in all_h2:
        bracket = bracket_h2.text.strip()
        sibling = bracket_h2.find_next_sibling()
        if sibling is None:
            continue

        if sibling.name == "h2":
            continue

        if sibling.name != "ul":
            raise RuntimeError("Unexpected sibling of <h2>", sibling)

        all_li = sibling.find_all("li")
        for match_li in all_li:
            match_text = match_li.text.strip()
            parts = match_text.split(" :: ")
            if len(parts) != 9:
                raise RuntimeError("Unexpected match text", match_text, event_name)

            (
                bout_type,
                winner_first_name,
                winner_last_name,
                winner_team,
                win_type,
                loser_first_name,
                loser_last_name,
                loser_team,
                score_summary,
            ) = parts

            if win_type == "won over":
                if score_summary != "OTHR1":
                    raise NotImplementedError(match_text)
                continue

            if win_type == "and":
                if score_summary != "DFF":  # Double Forfeit
                    raise NotImplementedError(match_text)
                continue

            if win_type not in _WIN_TYPE_MAP:
                raise NotImplementedError(match_text)

            result_type = _WIN_TYPE_MAP[win_type]
            if result_type is None:
                continue

            winner = f"{winner_first_name} {winner_last_name}"
            winner = winner.strip()

            loser = f"{loser_first_name} {loser_last_name}"
            loser = loser.strip()

            match_ = bracket_util.MatchV1(
                event_name=event_name,
                event_date=event_date,
                bracket=bracket,
                round_=bout_type,
                division=bracket_util.classify_bracket(bracket),
                winner=winner,
                winner_team=winner_team,
                loser=loser,
                loser_team=loser_team,
                result=score_summary,
                result_type=result_type,
                source="trackwrestling",
            )
            round_matches.append(match_)

        ul_count += 1

    if ul_count != len(all_ul):
        raise RuntimeError("Did not discover all <ul>", event_name)

    return round_matches


_DualMatchTuple = tuple[int, str, str, str]


class _DualMatchExtracted(_ForbidExtra):
    weight: int
    winner: str
    loser: str
    result: str

    def as_tuple(self) -> _DualMatchTuple:
        return self.weight, self.winner, self.loser, self.result


def _extract_match_li(match_li: bs4.Tag) -> _DualMatchExtracted | None:
    children = match_li.contents
    if len(children) != 5:
        return None

    before, span1, middle, span2, after = children
    middle_text = middle.text.strip()
    if middle_text != "over":
        breakpoint()
        return None

    if span1.name != "span" or span2.name != "span":
        return None

    before_text = before.text.strip()
    if not before_text.endswith(" -"):
        return None

    weight = int(before_text[:-2])
    winner = span1.text.strip()
    loser = span2.text.strip()
    result = after.text.strip()
    return _DualMatchExtracted(weight=weight, winner=winner, loser=loser, result=result)


_DualAthleteTuple = tuple[str, str]


class _DualAthlete(_ForbidExtra):
    name: str
    team: str

    def as_tuple(self) -> _DualAthleteTuple:
        return self.name, self.team

    def as_text(self) -> str:
        return f"{self.name} ({self.team})"


def _extract_dual_weight(
    html: str,
) -> tuple[list[_DualMatchExtracted], list[_DualAthlete]]:
    matches: list[_DualMatchExtracted] = []
    athletes: list[_DualAthlete] = []

    soup = bs4.BeautifulSoup(html, features="html.parser")

    all_li = soup.find_all("li")
    for match_li in all_li:
        if "Unknown (Unattached)" in match_li.text:
            continue
        if match_li.text in _ERRONEOUS_DUAL_MATCHES:
            continue

        extracted = _extract_match_li(match_li)
        if extracted is None:
            raise RuntimeError("Unexpected match <li>", match_li)

        matches.append(extracted)

    all_h2 = soup.find_all("h2")
    for athlete_h2 in all_h2:
        athlete_text = athlete_h2.text.strip()
        name, remaining = athlete_text.split(" of ")
        team, _ = remaining.split(" went ")
        athlete = _DualAthlete(name=name, team=team)
        athletes.append(athlete)

    return matches, athletes


def _extract_duals(
    weights_raw: dict[str, str],
) -> tuple[list[_DualMatchExtracted], list[_DualAthlete]]:
    known_matches: set[_DualMatchTuple] = set()
    all_extracted_matches: list[_DualMatchExtracted] = []

    known_athletes: set[_DualAthleteTuple] = set()
    all_extracted_athletes: list[_DualAthlete] = []

    weights = sorted(weights_raw.keys())
    for weight in weights:
        html = weights_raw[weight]
        extracted_matches, extracted_athletes = _extract_dual_weight(html)
        for match_ in extracted_matches:
            match_key = match_.as_tuple()
            if match_key not in known_matches:
                known_matches.add(match_key)
                all_extracted_matches.append(match_)

        for athlete in extracted_athletes:
            athlete_key = athlete.as_tuple()
            if athlete_key not in known_athletes:
                known_athletes.add(athlete_key)
                all_extracted_athletes.append(athlete)

    return all_extracted_matches, all_extracted_athletes


def _division_for_event(event_name: str) -> bracket_util.Division:
    if event_name == "2025 Hub City Hammer Duals":
        return "intermediate"
    if event_name == "The Didi Duals 2026":
        return "intermediate"

    raise NotImplementedError(event_name)


def _to_result_type(result: str) -> bracket_util.ResultType:
    if result.startswith("SV-1 "):
        return "overtime"
    if result.startswith("TB-1 "):
        return "overtime"
    if result.startswith("Dec "):
        return "decision"
    if result.startswith("Maj "):
        return "major"
    if result.startswith("TF "):
        return "tech"
    if result.startswith("Fall "):
        return "pin"
    raise NotImplementedError(result)


def _ignore_result(result: str) -> bool:
    if result.startswith("Inj "):
        return True
    if result.startswith("MFF"):  # noqa: SIM103
        return True

    return False


def parse_dual_event(
    weights_raw: dict[str, str], event_name: str, event_date: str
) -> list[bracket_util.MatchV1]:
    extracted_matches, extracted_athletes = _extract_duals(weights_raw)
    by_text = {athlete.as_text(): athlete for athlete in extracted_athletes}

    all_matches: list[bracket_util.MatchV1] = []

    for match_ in extracted_matches:
        result = match_.result
        if _ignore_result(result):
            continue

        winner_athlete = by_text[match_.winner]
        loser_athlete = by_text[match_.loser]

        all_matches.append(
            bracket_util.MatchV1(
                event_name=event_name,
                event_date=event_date,
                bracket=str(match_.weight),
                round_="Dual",
                division=_division_for_event(event_name),
                winner=winner_athlete.name,
                winner_team=winner_athlete.team,
                loser=loser_athlete.name,
                loser_team=loser_athlete.team,
                result=result,
                result_type=_to_result_type(result),
                source="trackwrestling_dual",
            )
        )

    return all_matches
