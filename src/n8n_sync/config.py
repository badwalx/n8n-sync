"""YAML configuration with explicit environment-only API keys."""

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError

from .errors import SyncError


class Instance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    api_key: SecretStr

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        from urllib.parse import urlsplit

        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("url must be an HTTP(S) URL without credentials, query, or fragment")
        return value.rstrip("/")


class Config(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid", env_prefix="N8N_SYNC_")
    instances: dict[str, Instance] = Field(min_length=1)
    credentials_map: dict[str, dict[str, str]] = Field(default_factory=dict)
    credential_ids: dict[str, dict[str, dict[str, str]]] = Field(default_factory=dict)
    workflow_dir: Path = Path("workflows")
    timeout: float = Field(default=30, gt=0)

    def instance(self, name: str | None) -> tuple[str, Instance]:
        if name is None and len(self.instances) == 1:
            name = next(iter(self.instances))
        if name not in self.instances:
            raise SyncError("Select --instance from: " + ", ".join(sorted(self.instances)))
        return name, self.instances[name]


def load_dotenv():
    """Load .env file if python-dotenv is available."""
    try:
        from dotenv import load_dotenv as _load
        _load()
    except ImportError:
        pass


def load_config(path: Path) -> Config:
    load_dotenv()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("instances"), dict):
            raise SyncError("Config must contain an instances mapping")
        for name, item in raw["instances"].items():
            if not isinstance(item, dict):
                raise SyncError(f"Invalid instance: {name}")
            key = item.get("api_key", "")
            match = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", str(key))
            if not match:
                raise SyncError(f"Instance {name}: api_key must use ${{ENV_VAR}}")
            value = os.environ.get(match[1])
            if not value:
                raise SyncError(f"Environment variable {match[1]} is missing or empty")
            item["api_key"] = value
        config = Config(**raw)
        if not config.workflow_dir.is_absolute():
            config.workflow_dir = path.resolve().parent / config.workflow_dir
        return config
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SyncError(f"Cannot read config {path}: {type(exc).__name__}") from exc
    except ValidationError as exc:
        # Never echo validation inputs: they may contain resolved API keys.
        details = "; ".join(
            ".".join(map(str, e["loc"])) + ": " + e["msg"] for e in exc.errors(include_input=False)
        )
        raise SyncError(f"Invalid config: {details}") from exc

    except SettingsError as exc:
        raise SyncError("Invalid N8N_SYNC_ environment setting") from exc
