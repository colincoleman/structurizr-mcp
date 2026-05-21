import hashlib
import hmac
import base64
import os
import time
from dataclasses import dataclass, field


@dataclass
class Config:
    structurizr_url: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_URL", "http://localhost:8080"))
    api_key: str | None = field(default_factory=lambda: os.environ.get("STRUCTURIZR_API_KEY"))
    api_secret: str | None = field(default_factory=lambda: os.environ.get("STRUCTURIZR_API_SECRET"))
    workspace_id: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_WORKSPACE_ID", "1"))
    workspace_dir: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_WORKSPACE_DIR", "."))

    def hmac_headers(self, method: str, path: str, body: bytes = b"") -> dict[str, str]:
        """
        Build X-Authorization / Nonce headers for the Structurizr vNext REST API.
        Returns an empty dict if no API key is configured (local mode with no auth).
        """
        if not self.api_key or not self.api_secret:
            return {}
        content_type = "application/json"
        nonce = str(int(time.time() * 1000))
        md5 = hashlib.md5(body).hexdigest()
        message = f"{method}\n{content_type}\n{md5}\n{nonce}\n{path}\n"
        signature = base64.b64encode(
            hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256).digest()
        ).decode()
        return {
            "X-Authorization": f"{self.api_key}:{signature}",
            "Nonce": nonce,
        }


config = Config()
