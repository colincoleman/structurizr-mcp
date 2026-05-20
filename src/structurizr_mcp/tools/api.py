import httpx
from structurizr_mcp.config import config


def _workspace_url() -> str:
    return f"{config.structurizr_url.rstrip('/')}/api/workspace/{config.workspace_id}"


def get_workspace_json() -> dict:
    """
    Fetch the current workspace model from the Structurizr REST API.

    Returns the full workspace as a parsed JSON dict, including all elements,
    relationships, and views.

    Works with structurizr/structurizr (local mode) — the successor to Structurizr Lite.
    """
    path = f"/api/workspace/{config.workspace_id}"
    headers = config.hmac_headers("GET", path)
    try:
        response = httpx.get(_workspace_url(), headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot connect to Structurizr at {config.structurizr_url}. "
            "Is the Docker container running? "
            "Start it with: docker run -it --rm -p 8080:8080 "
            "-v $PWD/architecture:/usr/local/structurizr structurizr/structurizr local"
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Structurizr API returned {e.response.status_code}: {e.response.text}")


def get_structurizr_status() -> dict:
    """
    Check whether Structurizr is reachable at the configured URL.

    Returns a dict with 'reachable' (bool), 'url' (str), and 'message' (str).
    """
    base_url = config.structurizr_url.rstrip("/")
    path = f"/api/workspace/{config.workspace_id}"
    headers = config.hmac_headers("GET", path)
    try:
        response = httpx.get(f"{base_url}{path}", headers=headers, timeout=5.0)
        reachable = response.status_code < 500
        return {
            "reachable": reachable,
            "url": base_url,
            "message": f"HTTP {response.status_code}",
        }
    except httpx.ConnectError:
        return {
            "reachable": False,
            "url": base_url,
            "message": "Connection refused — is the Docker container running?",
        }
    except httpx.TimeoutException:
        return {
            "reachable": False,
            "url": base_url,
            "message": "Connection timed out",
        }
