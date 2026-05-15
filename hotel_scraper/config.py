"""Configuration loading from YAML + .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class Config:
    raw: dict[str, Any]
    username: str | None
    password: str | None

    @property
    def base_url(self) -> str:
        return self.raw["site"]["base_url"]

    def url(self, path_key: str) -> str:
        return self.base_url.rstrip("/") + self.raw["site"][path_key]

    def selector(self, *keys: str) -> str:
        node: Any = self.raw["selectors"]
        for key in keys:
            node = node[key]
        return node

    def timeout(self, key: str) -> int:
        return int(self.raw["timeouts"][key])

    @property
    def output_dir(self) -> Path:
        return Path(self.raw["output"]["directory"])

    @property
    def filename_template(self) -> str:
        return self.raw["output"]["filename_template"]

    def reservation_status_code(self, label: str) -> str | None:
        return self.raw["reservation_status_codes"].get(label.lower())

    def reservation_type_code(self, label: str) -> str | None:
        return self.raw["reservation_type_codes"].get(label.lower())


def load(config_path: str | Path = "config.yaml", env_path: str | Path | None = ".env") -> Config:
    if env_path and Path(env_path).exists():
        load_dotenv(env_path)

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}. "
            "Copy config.example.yaml to config.yaml and edit it."
        )

    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return Config(
        raw=raw,
        username=os.getenv("SCRAPER_USERNAME") or None,
        password=os.getenv("SCRAPER_PASSWORD") or None,
    )
