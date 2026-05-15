"""Entry point for the hotel reservation scraper."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import auth
from . import config as config_module
from . import driver as driver_module
from . import extractors
from .config import Config
from .filters import FilterOptions, apply as apply_filters

log = logging.getLogger("hotel_scraper")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hotel-scraper",
        description=(
            "Scrape reservation details from a hotel reservation management system "
            "via Selenium and export them as JSON."
        ),
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--env", default=".env",
        help="Path to .env file for credentials (default: .env)",
    )
    parser.add_argument(
        "--filters", default=None,
        help="Path to a JSON file describing FilterOptions (default: no filters)",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run Chrome in headless mode",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override the output directory defined in config",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def load_filters(path: str | None) -> FilterOptions:
    if not path:
        return FilterOptions()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return FilterOptions(**data)


def run() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    try:
        cfg = config_module.load(args.config, args.env)
    except FileNotFoundError as e:
        log.error("%s", e)
        return 2

    output_dir = Path(args.output_dir) if args.output_dir else cfg.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    filter_options = load_filters(args.filters)

    driver = driver_module.build(
        headless=args.headless,
        implicit_wait=cfg.timeout("implicit_wait"),
    )

    try:
        auth.login(driver, cfg)
        apply_filters(driver, cfg, filter_options)
        scraped = scrape_all_details(driver, cfg, output_dir)
        log.info("Done. Scraped %d reservation(s) into %s", scraped, output_dir)
        return 0
    except Exception:
        log.exception("Scraper failed")
        return 1
    finally:
        driver.quit()


def scrape_all_details(driver: WebDriver, cfg: Config, output_dir: Path) -> int:
    detail_class = cfg.selector("filters", "detail_button_class")
    detail_buttons = driver.find_elements(By.CLASS_NAME, detail_class)

    if not detail_buttons:
        log.warning(
            "No reservations found. Check your date range (max 3 months) and filters."
        )
        return 0

    main_window = driver.current_window_handle
    page_load = cfg.timeout("page_load")
    total = len(detail_buttons)
    scraped = 0

    log.info("Found %d reservation(s)", total)

    for index in range(total):
        try:
            # Re-query each iteration to avoid stale element references after
            # opening/closing the detail window.
            buttons = driver.find_elements(By.CLASS_NAME, detail_class)
            if index >= len(buttons):
                log.warning("Reservation %d/%d disappeared from DOM, skipping", index + 1, total)
                continue
            buttons[index].click()

            WebDriverWait(driver, page_load).until(EC.number_of_windows_to_be(2))
            new_window = next(h for h in driver.window_handles if h != main_window)
            driver.switch_to.window(new_window)

            detail = extractors.extract_reservation_detail(driver)
            voucher = (detail.get("summary") or {}).get("voucher") or f"index_{index}"
            voucher_safe = _safe_filename_token(voucher)
            filename = cfg.filename_template.format(voucher=voucher_safe)

            (output_dir / filename).write_text(
                json.dumps(detail, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            log.info("[%d/%d] Saved %s", index + 1, total, filename)
            scraped += 1
        except (NoSuchElementException, TimeoutException) as e:
            log.warning("[%d/%d] Skipped due to %s", index + 1, total, type(e).__name__)
        except Exception as e:
            log.exception("[%d/%d] Unexpected error: %s", index + 1, total, e)
        finally:
            try:
                if driver.current_window_handle != main_window:
                    driver.close()
                driver.switch_to.window(main_window)
            except Exception:
                log.exception("Failed to return to main window")

    return scraped


def _safe_filename_token(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in value.strip())


if __name__ == "__main__":
    sys.exit(run())
