from pathlib import Path
from structurizr_mcp.config import config


def _resolve(path: str, workspace: str | None = None) -> Path:
    """Resolve path relative to the (optionally workspace-scoped) base; reject traversal attempts."""
    base = config.effective_workspace_dir(workspace)
    resolved = (base / path).resolve()
    if not str(resolved).startswith(str(base)):
        raise ValueError(f"Path '{path}' escapes the workspace directory")
    return resolved


def read_dsl_file(path: str, workspace: str | None = None) -> str:
    """Read a Structurizr DSL file and return its contents."""
    resolved = _resolve(path, workspace)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved.read_text(encoding="utf-8")


def write_dsl_file(path: str, content: str, workspace: str | None = None) -> str:
    """Write content to a DSL file, creating parent directories as needed."""
    resolved = _resolve(path, workspace)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return f"Written to {resolved}"


def list_dsl_files(directory: str = ".", workspace: str | None = None) -> list[str]:
    """List all .dsl files under a directory (relative to the workspace)."""
    resolved = _resolve(directory, workspace)
    if not resolved.is_dir():
        raise NotADirectoryError(f"Not a directory: {resolved}")
    base = config.effective_workspace_dir(workspace)
    return [str(p.relative_to(base)) for p in sorted(resolved.rglob("*.dsl"))]
