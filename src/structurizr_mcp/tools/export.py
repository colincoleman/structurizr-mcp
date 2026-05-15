import subprocess
from pathlib import Path
from structurizr_mcp.config import config
from structurizr_mcp.tools.dsl import _resolve

SUPPORTED_FORMATS = ("mermaid", "plantuml", "c4plantuml", "svg", "png", "dot")


def export_diagrams(path: str, format: str = "mermaid", output_dir: str | None = None) -> dict:
    """
    Export diagrams from a Structurizr DSL file using structurizr-cli.

    Args:
        path: Path to the .dsl file (relative to workspace_dir).
        format: Output format — mermaid (default), plantuml, c4plantuml, svg, png, dot.
        output_dir: Directory for exported files (relative to workspace_dir). Defaults to same dir as the DSL file.

    Returns a dict with 'files' (list of output paths) and 'output' (raw CLI output).
    """
    fmt = format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{format}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")

    resolved = _resolve(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    if output_dir is None:
        out_resolved = resolved.parent
    else:
        out_resolved = _resolve(output_dir)
        out_resolved.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            config.cli_path,
            "export",
            "--workspace", str(resolved),
            "--format", fmt,
            "--output", str(out_resolved),
        ],
        capture_output=True,
        text=True,
    )

    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(f"structurizr-cli export failed:\n{output}")

    extension_map = {
        "mermaid": ".md",
        "plantuml": ".puml",
        "c4plantuml": ".puml",
        "svg": ".svg",
        "png": ".png",
        "dot": ".dot",
    }
    ext = extension_map[fmt]
    files = [str(p) for p in sorted(out_resolved.glob(f"*{ext}"))]

    return {"files": files, "output": output}
