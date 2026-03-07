import json
import pathlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

import bracket_util
import usabracketing

_WAIT_TIME = 3
_HERE = pathlib.Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent


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


def main() -> None:
    login_info = usabracketing.get_login_info()

    event = bracket_util.Event(
        name="IKWF West Chicago Sectional", start_date=None, end_date="2026-03-07"
    )
    driver = usabracketing._open_event(event, login_info)
    _click_brackets(driver)
    bracket_hrefs = _get_brackets_list(driver)

    captured: dict[str, str] = {}
    for bracket_href in bracket_hrefs:
        if bracket_href in captured:
            raise RuntimeError("Duplicate URL", bracket_href)
        html = _get_bracket_html(driver, bracket_href)
        captured[bracket_href] = html

    driver.quit()

    filename = _ROOT / "_raw-data" / "bracket-parsing" / "examples.json"
    with open(filename, "w") as file_obj:
        json.dump(captured, file_obj, indent=2, sort_keys=True)
        file_obj.write("\n")


if __name__ == "__main__":
    main()
