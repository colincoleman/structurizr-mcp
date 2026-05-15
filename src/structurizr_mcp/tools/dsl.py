from pathlib import Path
from structurizr_mcp.config import config


def _resolve(path: str) -> Path:
    """Resolve path relative to workspace_dir; reject traversal attempts."""
    base = Path(config.workspace_dir).resolve()
    resolved = (base / path).resolve()
    if not str(resolved).startswith(str(base)):
        raise ValueError(f"Path '{path}' escapes the workspace directory")
    return resolved


def read_dsl_file(path: str) -> str:
    """Read a Structurizr DSL file and return its contents."""
    resolved = _resolve(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved.read_text(encoding="utf-8")


def write_dsl_file(path: str, content: str) -> str:
    """Write content to a DSL file, creating parent directories as needed."""
    resolved = _resolve(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return f"Written to {resolved}"


def list_dsl_files(directory: str = ".") -> list[str]:
    """List all .dsl files under a directory (relative to workspace_dir)."""
    resolved = _resolve(directory)
    if not resolved.is_dir():
        raise NotADirectoryError(f"Not a directory: {resolved}")
    base = Path(config.workspace_dir).resolve()
    return [str(p.relative_to(base)) for p in sorted(resolved.rglob("*.dsl"))]
