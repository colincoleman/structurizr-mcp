import subprocess
from pathlib import Path
from structurizr_mcp.config import config
from structurizr_mcp.tools.dsl import _resolve


def validate_workspace(path: str) -> dict:
    """
    Validate a Structurizr DSL file using structurizr-cli.

    Returns a dict with 'valid' (bool), 'errors' (list of str), and 'output' (raw CLI output).
    """
    resolved = _resolve(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    result = subprocess.run(
        [config.cli_path, "validate", "--workspace", str(resolved)],
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
