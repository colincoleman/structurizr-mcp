import subprocess
from pathlib import Path
from structurizr_mcp.config import config
from structurizr_mcp.tools.dsl import _resolve

DOCKER_IMAGE = "structurizr/structurizr"
CONTAINER_WORKSPACE = "/usr/local/structurizr"

# Formats exported purely from the DSL — no running Structurizr server needed.
CLI_ONLY_FORMATS = ("mermaid", "plantuml", "c4plantuml", "json", "static", "websequencediagrams")
# Formats rendered by the Structurizr web UI — require a running server at STRUCTURIZR_URL.
SERVER_FORMATS = ("svg", "png")

SUPPORTED_FORMATS = CLI_ONLY_FORMATS + SERVER_FORMATS

_EXTENSION_MAP = {
    "mermaid": ".md",
    "plantuml": ".puml",
    "c4plantuml": ".puml",
    "svg": ".svg",
    "png": ".png",
    "json": ".json",
    "static": ".html",
    "websequencediagrams": ".txt",
}


def _container_path(local: Path, workspace_dir: Path) -> str:
    """Translate a local absolute path to its equivalent inside the Docker container."""
    return f"{CONTAINER_WORKSPACE}/{local.relative_to(workspace_dir)}"


def _docker_url(url: str) -> str:
    """Replace localhost/127.0.0.1 with host.docker.internal so containers can reach the host."""
    return url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")


def export_diagrams(path: str, format: str = "mermaid", output_dir: str | None = None) -> dict:
    """
    Export diagrams from a Structurizr DSL file via Docker (structurizr/structurizr export).

    SVG and PNG formats require Structurizr to be running at STRUCTURIZR_URL
    (default http://localhost:8080). All other formats work without a server.

    Args:
        path: Path to the .dsl file (relative to STRUCTURIZR_WORKSPACE_DIR).
        format: Output format — mermaid (default), plantuml, c4plantuml,
                svg, png, json, static, websequencediagrams.
        output_dir: Where to write exported files (relative to STRUCTURIZR_WORKSPACE_DIR).
                    Defaults to the same directory as the DSL file.

    Returns a dict with 'files' (list of output paths) and 'output' (raw CLI output).
    """
    fmt = format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{format}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")

    workspace_dir = Path(config.workspace_dir).resolve()
    resolved = _resolve(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    if output_dir is None:
        out_resolved = resolved.parent
    else:
        out_resolved = _resolve(output_dir)
        out_resolved.mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run", "--rm",
        "--add-host=host.docker.internal:host-gateway",
        "-v", f"{workspace_dir}:{CONTAINER_WORKSPACE}",
        DOCKER_IMAGE, "export",
        "-w", _container_path(resolved, workspace_dir),
        "-f", fmt,
        "-o", _container_path(out_resolved, workspace_dir),
    ]

    if fmt in SERVER_FORMATS:
        cmd += ["-url", _docker_url(config.structurizr_url)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(f"Structurizr export failed:\n{output}")

    ext = _EXTENSION_MAP.get(fmt, f".{fmt}")
    files = [str(p) for p in sorted(out_resolved.glob(f"*{ext}"))]

    return {"files": files, "output": output}
