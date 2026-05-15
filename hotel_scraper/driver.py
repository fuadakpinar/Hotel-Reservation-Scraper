"""WebDriver factory."""

from __future__ import annotations

import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

log = logging.getLogger(__name__)


def build(headless: bool = False, implicit_wait: int = 10) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    log.info("Starting Chrome driver (headless=%s)", headless)
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(implicit_wait)
    return driver
