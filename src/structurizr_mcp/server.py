from mcp.server.fastmcp import FastMCP
from structurizr_mcp.tools.dsl import read_dsl_file, write_dsl_file, list_dsl_files
from structurizr_mcp.tools.validate import validate_workspace
from structurizr_mcp.tools.export import export_diagrams, SUPPORTED_FORMATS
from structurizr_mcp.tools.api import get_workspace_json, get_structurizr_status

mcp = FastMCP("structurizr")


@mcp.tool()
def read_dsl(path: str) -> str:
    """Read a Structurizr DSL file. Path is relative to STRUCTURIZR_WORKSPACE_DIR."""
    return read_dsl_file(path)


@mcp.tool()
def write_dsl(path: str, content: str) -> str:
    """
    Write or overwrite a Structurizr DSL file. Path is relative to STRUCTURIZR_WORKSPACE_DIR.
    Creates parent directories as needed. Structurizr Lite will pick up the change automatically
    if it is currently running.
    """
    return write_dsl_file(path, content)


@mcp.tool()
def list_dsl(directory: str = ".") -> list[str]:
    """
    List all .dsl files under a directory. Path is relative to STRUCTURIZR_WORKSPACE_DIR.
    Returns paths relative to STRUCTURIZR_WORKSPACE_DIR.
    """
    return list_dsl_files(directory)


@mcp.tool()
def validate(path: str) -> dict:
    """
    Validate a Structurizr DSL file using structurizr-cli.
    Returns {valid: bool, errors: [str], output: str}.
    Requires structurizr-cli to be installed and on PATH (or set STRUCTURIZR_CLI).
    """
    return validate_workspace(path)


@mcp.tool()
def export(path: str, format: str = "mermaid", output_dir: str | None = None) -> dict:
    """
    Export diagrams from a DSL file using structurizr-cli.

    Args:
        path: Path to the .dsl file (relative to STRUCTURIZR_WORKSPACE_DIR).
        format: Output format. One of: mermaid (default), plantuml, c4plantuml, svg, png, dot.
        output_dir: Where to write exported files (relative to STRUCTURIZR_WORKSPACE_DIR).
                    Defaults to the same directory as the DSL file.

    Returns {files: [str], output: str}.
    Mermaid output is ideal for embedding in markdown documentation.
    """
    return export_diagrams(path, format, output_dir)


@mcp.tool()
def workspace_json() -> dict:
    """
    Fetch the current workspace model from Structurizr Lite's REST API (GET /api/workspace).
    Returns the full architecture model as JSON: all elements, relationships, and views.
    Requires Structurizr Lite to be running (STRUCTURIZR_URL, default http://localhost:8080).
    """
    return get_workspace_json()


@mcp.tool()
def structurizr_status() -> dict:
    """
    Check whether Structurizr Lite is reachable at the configured URL.
    Returns {reachable: bool, url: str, message: str}.
    """
    return get_structurizr_status()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
