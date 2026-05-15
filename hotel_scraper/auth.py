"""Login flow."""

from __future__ import annotations

import getpass
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from .config import Config

log = logging.getLogger(__name__)


def login(driver: WebDriver, config: Config) -> None:
    url = config.url("login_path")
    log.info("Navigating to login page: %s", url)
    driver.get(url)

    username = config.username or input("Username: ").strip()
    password = config.password or getpass.getpass("Password: ")

    if not username or not password:
        raise ValueError("Username and password are required.")

    log.info("Submitting credentials")
    driver.find_element(By.ID, config.selector("login", "username")).send_keys(username)
    password_field = driver.find_element(By.ID, config.selector("login", "password"))
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    driver.get(config.url("reservations_path"))
    log.info("Reached reservations page")
