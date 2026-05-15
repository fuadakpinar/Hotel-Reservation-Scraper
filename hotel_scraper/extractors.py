"""Parse reservation detail pages into structured dicts."""

from __future__ import annotations

import logging
from typing import Any

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

log = logging.getLogger(__name__)

STAY_KEYS = (
    "operator",
    "check_in",
    "check_out",
    "room_type",
    "accomodation_type",
    "board",
    "adult",
    "child",
    "baby",
    "pax",
    "room_count",
    "sale_date",
    "first_sent_date",
)

CUSTOMER_KEYS = (
    "title",
    "nationality",
    "first_name",
    "sur_name",
    "birth_date",
    "age",
    "pass_serial_no",
    "pass_no",
    "arrival_time",
    "departure_time",
)


def extract_reservation_detail(driver: WebDriver) -> dict[str, Any]:
    """Extract a single reservation detail page.

    Assumes the driver is already focused on the detail window.
    """
    header = {
        "title": _safe_text(driver, "body > div.well.well-small > h4"),
        "subtitle": _safe_text(driver, "body > div.well.well-small > h5"),
        "section": _safe_text(driver, "body > div.well.well-small > h6"),
    }

    summary_cells = _row_cells(driver, "body > table:nth-child(3) > tbody > tr")
    summary = (
        {
            "voucher": summary_cells[0],
            "sale_date": summary_cells[1],
            "reservation_confirm_status": summary_cells[2],
            "reservation_type": summary_cells[3],
        }
        if len(summary_cells) >= 4
        else {}
    )

    stay_cells = _row_cells(driver, "body > table:nth-child(4) > tbody > tr")
    stay = dict(zip(STAY_KEYS, stay_cells))

    customers = _extract_customers(driver)

    notes = {
        "agency_note": _safe_text(driver, "body > table:nth-child(6) > tbody > tr > td"),
        "hotel_note": _safe_text(driver, "body > table:nth-child(7) > tbody > tr > td"),
        "conditions": _safe_text(driver, "body > table:nth-child(8) > tbody > tr > td"),
    }

    return {
        "header": header,
        "summary": summary,
        "stay": stay,
        "customers": customers,
        "notes": notes,
    }


def _safe_text(driver: WebDriver, css_selector: str) -> str:
    try:
        return driver.find_element(By.CSS_SELECTOR, css_selector).text
    except NoSuchElementException:
        return ""


def _row_cells(driver: WebDriver, row_selector: str) -> list[str]:
    try:
        row = driver.find_element(By.CSS_SELECTOR, row_selector)
    except NoSuchElementException:
        return []
    return [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]


def _extract_customers(driver: WebDriver) -> list[dict[str, str]]:
    try:
        table = driver.find_element(By.CSS_SELECTOR, "body > table:nth-child(5)")
    except NoSuchElementException:
        return []

    rows = table.find_elements(By.CSS_SELECTOR, "tbody > tr")
    customers: list[dict[str, str]] = []
    for row in rows:
        cells = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
        if not cells:
            continue
        customers.append(dict(zip(CUSTOMER_KEYS, cells)))
    return customers
