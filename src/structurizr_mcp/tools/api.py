import httpx
from structurizr_mcp.config import config


def get_workspace_json() -> dict:
    """
    Fetch the current workspace model from Structurizr Lite's REST API.

    Returns the full workspace as a parsed JSON dict, including all elements,
    relationships, and views.
    """
    url = f"{config.structurizr_url.rstrip('/')}/api/workspace"
    try:
        response = httpx.get(url, auth=config.auth, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot connect to Structurizr Lite at {config.structurizr_url}. "
            "Is the Docker container running?"
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Structurizr API returned {e.response.status_code}: {e.response.text}")


def get_structurizr_status() -> dict:
    """
    Check whether Structurizr Lite is reachable at the configured URL.

    Returns a dict with 'reachable' (bool), 'url' (str), and 'message' (str).
    """
    url = config.structurizr_url.rstrip("/")
    try:
        response = httpx.get(f"{url}/api/workspace", auth=config.auth, timeout=5.0)
        reachable = response.status_code < 500
        return {
            "reachable": reachable,
            "url": url,
            "message": f"HTTP {response.status_code}",
        }
    except httpx.ConnectError:
        return {
            "reachable": False,
            "url": url,
            "message": "Connection refused — is the Docker container running?",
        }
    except httpx.TimeoutException:
        return {
            "reachable": False,
            "url": url,
            "message": "Connection timed out",
        }
