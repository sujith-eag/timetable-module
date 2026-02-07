"""
Application settings management using Pydantic.

This module provides centralized configuration management with:
- Environment variable loading (TIMETABLE_* prefix)
- Type validation
- Default values
- Singleton pattern for global access
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid log levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Module-level cache for singleton pattern
_settings_instance: Optional["Settings"] = None


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables with TIMETABLE_ prefix.
    For example: TIMETABLE_LOG_LEVEL=DEBUG, TIMETABLE_DATA_DIR=/path/to/data
    """

    model_config = SettingsConfigDict(
        env_prefix="TIMETABLE_",
        case_sensitive=False,
        extra="ignore",
    )

    # Core paths
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / "timetable-data",
        description="Root directory containing stage data",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file: Optional[Path] = Field(
        default=None,
        description="Path to log file. If None, logs only to console",
    )
    log_format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        description="Log message format string",
    )

    # Behavior flags
    strict_mode: bool = Field(
        default=False,
        description="If True, treat warnings as errors during validation",
    )
    verbose: bool = Field(
        default=False,
        description="If True, output more detailed information",
    )

    # Stage configuration
    active_semesters: list[int] = Field(
        default=[1, 3],
        description="Semesters to process (odd=1,3,5,7; even=2,4,6,8)",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        """Normalize log level to uppercase and validate."""
        if isinstance(v, str):
            v = v.upper()
            valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if v not in valid_levels:
                raise ValueError(
                    f"Invalid log level '{v}'. Must be one of: {', '.join(valid_levels)}"
                )
        return v

    @field_validator("data_dir", mode="before")
    @classmethod
    def resolve_data_dir(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects and resolve."""
        if isinstance(v, str):
            v = Path(v)
        return v.resolve() if v else Path.cwd()

    @model_validator(mode="after")
    def validate_paths(self) -> "Settings":
        """Validate that required paths exist or can be created."""
        # Note: We don't require paths to exist at settings creation time
        # This allows settings to be created before directories exist
        return self

    def stage_dir(self, stage: int) -> Path:
        """
        Get the directory path for a specific stage.

        Args:
            stage: Stage number (1-6)

        Returns:
            Path to the stage directory

        Raises:
            ValueError: If stage number is invalid
        """
        if stage < 1 or stage > 6:
            raise ValueError(f"Invalid stage number: {stage}. Must be 1-6.")
        return self.data_dir / f"stage_{stage}"

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory path."""
        return self.data_dir / "logs"

    @property
    def output_dir(self) -> Path:
        """Get the output directory path (alias for logs_dir)."""
        return self.logs_dir

    @property
    def schemas_dir(self) -> Path:
        """Get the JSON schemas directory path."""
        return self.data_dir / "schemas"

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.log_level == "DEBUG"

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.schemas_dir.mkdir(parents=True, exist_ok=True)
        for stage in range(1, 7):
            self.stage_dir(stage).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the application settings (singleton).

    This function returns a cached Settings instance.
    On first call, it loads settings from environment variables and .env file.

    Returns:
        The Settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.data_dir)
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings() -> None:
    """
    Reset the settings cache.

    Useful for testing or when environment variables change.
    """
    global _settings_instance
    _settings_instance = None
    get_settings.cache_clear()
