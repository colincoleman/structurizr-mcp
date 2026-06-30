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
    # Base directory that bounds all file access (the sandbox root). When several workspaces
    # live side by side, point this at their common parent and select one per call via the
    # `workspace` tool argument (or the STRUCTURIZR_DEFAULT_WORKSPACE fallback below).
    workspace_dir: str = field(default_factory=lambda: os.environ.get("STRUCTURIZR_WORKSPACE_DIR", "."))
    # Optional sub-directory under workspace_dir used when a tool call omits `workspace`.
    default_workspace: str | None = field(default_factory=lambda: os.environ.get("STRUCTURIZR_DEFAULT_WORKSPACE") or None)

    def effective_workspace_dir(self, workspace: str | None = None) -> "Path":
        """
        Resolve the working directory for a call: workspace_dir / (workspace or default_workspace).

        Returns workspace_dir itself when neither is set. Raises if the result escapes
        workspace_dir, so a caller can never reach outside the configured base.
        """
        from pathlib import Path
        base = Path(self.workspace_dir).resolve()
        ws = workspace if workspace is not None else self.default_workspace
        if ws:
            resolved = (base / ws).resolve()
            if not str(resolved).startswith(str(base)):
                raise ValueError(f"Workspace '{ws}' escapes the base directory {base}")
            return resolved
        return base

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
