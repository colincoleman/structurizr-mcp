import subprocess
from pathlib import Path
from structurizr_mcp.config import config
from structurizr_mcp.tools.dsl import _resolve
from structurizr_mcp.tools.export import DOCKER_IMAGE, CONTAINER_WORKSPACE, _container_path


def validate_workspace(path: str) -> dict:
    """
    Validate a Structurizr DSL file via Docker (structurizr/structurizr validate).
    Returns a dict with 'valid' (bool), 'errors' (list of str), and 'output' (raw CLI output).
    """
    workspace_dir = Path(config.workspace_dir).resolve()
    resolved = _resolve(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{workspace_dir}:{CONTAINER_WORKSPACE}",
            DOCKER_IMAGE, "validate",
            "-w", _container_path(resolved, workspace_dir),
        ],
        capture_output=True,
        text=True,
    )

    output = (result.stdout + result.stderr).strip()
    valid = result.returncode == 0
    errors = _parse_errors(result.stderr or result.stdout)

    return {"valid": valid, "errors": errors, "output": output}


def _parse_errors(text: str) -> list[str]:
    """Extract error lines from CLI output."""
    errors = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and any(word in stripped.lower() for word in ("error", "warning", "invalid", "unexpected")):
            errors.append(stripped)
    return errors
