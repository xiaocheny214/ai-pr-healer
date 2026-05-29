"""Configuration management for healpr."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """healpr configuration."""

    github_token: str = ""
    work_dir: Path = field(default_factory=lambda: Path("/tmp/healpr-workspace"))

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        token = os.environ.get("HEALPR_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
        work_dir = os.environ.get("HEALPR_WORK_DIR", "/tmp/healpr-workspace")
        return cls(
            github_token=token,
            work_dir=Path(work_dir),
        )

    def ensure_work_dir(self):
        """Create work directory if it doesn't exist."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
