# Hotel Reservation Scraper

A configurable Selenium-based scraper for hotel reservation management
systems. It logs in, applies a set of optional filters (date ranges,
reservation status/type, voucher number, hotel and agency exclusions),
then walks through every reservation in the result list and exports the
full detail page — including the guest table and operational notes — as
structured JSON.

Originally built as a freelance project; rewritten as a clean,
config-driven tool suitable for adapting to any similar reservation
backend.

---

## Features

- **YAML configuration** for site URLs, DOM selectors, and timeouts —
  no code changes needed to point it at a different system.
- **.env support** for credentials (or interactive `getpass` prompt).
- **CLI** with headless mode, log levels, and a JSON-driven filter file.
- **Robust extraction loop** — each reservation is scraped in isolation,
  errors on one row don't kill the rest.
- **Stale-element safe** — the detail button list is re-queried each
  iteration after window switching.
- **Per-reservation JSON output**, named by voucher number for easy
  downstream processing.

## Project structure

```
hotel-reservation-scraper/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── config.example.yaml      # site, selectors, timeouts, output settings
├── .env.example             # optional credentials
├── filters.example.json     # optional reservation filters
├── hotel_scraper/
│   ├── __init__.py
│   ├── __main__.py          # python -m hotel_scraper
│   ├── main.py              # CLI entry point
│   ├── config.py            # YAML + .env loader
│   ├── driver.py            # Chrome WebDriver factory
│   ├── auth.py              # login flow
│   ├── filters.py           # filter form handling
│   └── extractors.py        # detail page parsing
└── output/                  # scraped JSON lands here (gitignored)
```

## Requirements

- Python 3.10+
- Google Chrome
- ChromeDriver matching your Chrome version (Selenium 4 will manage this
  automatically via Selenium Manager on modern installs)

## Setup

```bash
git clone https://github.com/fuadakpinar/hotel-reservation-scraper.git
cd hotel-reservation-scraper

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml
cp .env.example .env          # optional, credentials can be entered at runtime
```

Edit `config.yaml` so that `site.base_url`, `site.login_path`,
`site.reservations_path` and the `selectors` block match the target
reservation system.

## Usage

Basic interactive run (it will prompt for username + password):

```bash
python -m hotel_scraper
```

Headless run with a filter file:

```bash
python -m hotel_scraper --headless --filters filters.example.json
```

All CLI options:

```
--config PATH         Path to YAML configuration file (default: config.yaml)
--env PATH            Path to .env file (default: .env)
--filters PATH        Path to a JSON filter file (default: no filters)
--headless            Run Chrome in headless mode
--output-dir DIR      Override the output directory defined in config
--log-level LEVEL     DEBUG | INFO | WARNING | ERROR (default: INFO)
```

## Filters

Filters are described in a JSON file matching the `FilterOptions`
dataclass. See [`filters.example.json`](filters.example.json):

```json
{
  "begin_checkin": "01.06.2024",
  "end_checkin": "31.08.2024",
  "reservation_status": "confirmed",
  "reservation_type": "new",
  "excluded_hotels": [],
  "excluded_agencies": []
}
```

Valid values:

| Field                 | Format                                   |
| --------------------- | ---------------------------------------- |
| Date fields           | `dd.mm.yyyy` (e.g. `01.06.2024`)         |
| `reservation_status`  | `confirmed`, `pending`, `not_confirmed`  |
| `reservation_type`    | `new`, `modified`, `canceled`            |
| `excluded_hotels`     | List of hotel names to uncheck           |
| `excluded_agencies`   | List of agency names to uncheck          |

Empty strings / empty lists mean "no filter on this field".

> The target system enforces a maximum date range of three months.

## Output

Each reservation produces a JSON file like:

```json
{
  "header": {"title": "...", "subtitle": "...", "section": "..."},
  "summary": {
    "voucher": "ABC123",
    "sale_date": "...",
    "reservation_confirm_status": "...",
    "reservation_type": "..."
  },
  "stay": {
    "operator": "...", "check_in": "...", "check_out": "...",
    "room_type": "...", "accomodation_type": "...", "board": "...",
    "adult": "2", "child": "0", "baby": "0", "pax": "2", "room_count": "1",
    "sale_date": "...", "first_sent_date": "..."
  },
  "customers": [
    {
      "title": "Mr", "nationality": "...", "first_name": "...",
      "sur_name": "...", "birth_date": "...", "age": "...",
      "pass_serial_no": "...", "pass_no": "...",
      "arrival_time": "...", "departure_time": "..."
    }
  ],
  "notes": {
    "agency_note": "...",
    "hotel_note": "...",
    "conditions": "..."
  }
}
```

Files are saved as `reservation_<voucher>.json` under the `output/`
directory by default.

## Adapting to a different system

The tool is structured so that **only `config.yaml` should need to
change** for sites with similar layouts (login form + filtered list +
per-row detail window). For sites with a noticeably different DOM, you
will most likely also need to adjust selectors in `hotel_scraper/extractors.py`.

## Status

This is a portfolio / showcase repository. The tool was originally written
several years ago for a private hotel reservation backend and has since
been rewritten as a generalised, configurable scraper. The example domain
and selectors in `config.example.yaml` are placeholders — the project
does not target any specific real-world system, and the original target
may no longer be online. Drop your own values into `config.yaml` to
adapt it to a similar backend.

## Notes

- Credentials are never stored — `.env` is gitignored, and interactive
  input goes through `getpass`.
- The example domain in `config.example.yaml` is a placeholder; this
  repository does not target any specific real-world system.

## License

[MIT](LICENSE) © Fuad AKPINAR
