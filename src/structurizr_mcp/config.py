import os
from dataclasses import dataclass, field


@dataclass
class Config:
    structurizr_url: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_URL", "http://localhost:8080"))
    api_key: str | None = field(default_factory=lambda: os.environ.get("STRUCTURIZR_API_KEY"))
    api_secret: str | None = field(default_factory=lambda: os.environ.get("STRUCTURIZR_API_SECRET"))
    workspace_dir: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_WORKSPACE_DIR", "."))
    cli_path: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_CLI", "structurizr-cli"))

    @property
    def auth(self) -> tuple[str, str] | None:
        if self.api_key and self.api_secret:
            return (self.api_key, self.api_secret)
        return None


config = Config()
