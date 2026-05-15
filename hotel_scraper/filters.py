"""Reservation list filters."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from .config import Config

log = logging.getLogger(__name__)

DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

DATE_FIELDS = (
    "begin_checkin",
    "begin_checkout",
    "end_checkin",
    "end_checkout",
    "begin_confirm",
    "end_confirm",
)


@dataclass
class FilterOptions:
    begin_checkin: str = ""
    begin_checkout: str = ""
    end_checkin: str = ""
    end_checkout: str = ""
    begin_confirm: str = ""
    end_confirm: str = ""
    voucher_no: str = ""
    # One of: "confirmed" | "pending" | "not_confirmed" | "" (any)
    reservation_status: str = ""
    # One of: "new" | "modified" | "canceled" | "" (any)
    reservation_type: str = ""
    # Names of items to uncheck in the multi-select dropdowns.
    excluded_hotels: list[str] = field(default_factory=list)
    excluded_agencies: list[str] = field(default_factory=list)


def _validate_date(value: str, field_name: str) -> None:
    if value and not DATE_RE.match(value):
        raise ValueError(
            f"{field_name} must be in dd.mm.yyyy format (e.g. 01.06.2024), got: {value!r}"
        )


def apply(driver: WebDriver, config: Config, options: FilterOptions) -> None:
    if options.excluded_hotels:
        log.info("Excluding %d hotel(s)", len(options.excluded_hotels))
        _toggle_dropdown_items(
            driver,
            dropdown_selector=config.selector("filters", "hotels_dropdown"),
            options_xpath=config.selector("filters", "hotels_options"),
            to_uncheck=set(options.excluded_hotels),
        )

    if options.excluded_agencies:
        log.info("Excluding %d agency/agencies", len(options.excluded_agencies))
        _toggle_dropdown_items(
            driver,
            dropdown_selector=config.selector("filters", "agencies_dropdown"),
            options_xpath=config.selector("filters", "agencies_options"),
            to_uncheck=set(options.excluded_agencies),
        )

    for field_key in DATE_FIELDS:
        value = getattr(options, field_key)
        if not value:
            continue
        _validate_date(value, field_key)
        element = driver.find_element(By.ID, config.selector("filters", field_key))
        driver.execute_script(
            "arguments[0].setAttribute('value', arguments[1])", element, value
        )

    if options.voucher_no:
        driver.find_element(By.ID, config.selector("filters", "voucher_no")).send_keys(
            options.voucher_no
        )

    if options.reservation_status:
        code = config.reservation_status_code(options.reservation_status)
        if code is None:
            raise ValueError(
                f"Unknown reservation_status: {options.reservation_status!r}. "
                "Expected one of: confirmed, pending, not_confirmed."
            )
        Select(
            driver.find_element(By.ID, config.selector("filters", "reservation_status"))
        ).select_by_value(code)

    if options.reservation_type:
        code = config.reservation_type_code(options.reservation_type)
        if code is None:
            raise ValueError(
                f"Unknown reservation_type: {options.reservation_type!r}. "
                "Expected one of: new, modified, canceled."
            )
        Select(
            driver.find_element(By.ID, config.selector("filters", "reservation_type"))
        ).select_by_value(code)

    log.info("Submitting filter form")
    driver.find_element(By.ID, config.selector("filters", "submit")).click()


def _toggle_dropdown_items(
    driver: WebDriver,
    dropdown_selector: str,
    options_xpath: str,
    to_uncheck: set[str],
) -> None:
    driver.find_element(By.CSS_SELECTOR, dropdown_selector).click()
    items = driver.find_elements(By.XPATH, options_xpath)
    for item in items:
        label = item.text.strip()
        if not label or label.lower() == "select all":
            continue
        if label in to_uncheck:
            item.click()
