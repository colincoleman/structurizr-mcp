from mcp.server.fastmcp import FastMCP
from structurizr_mcp.tools.dsl import read_dsl_file, write_dsl_file, list_dsl_files
from structurizr_mcp.tools.validate import validate_workspace
from structurizr_mcp.tools.export import export_diagrams, SUPPORTED_FORMATS
from structurizr_mcp.tools.api import get_workspace_json, get_structurizr_status

mcp = FastMCP("structurizr")


@mcp.tool()
def read_dsl(path: str, workspace: str | None = None) -> str:
    """
    Read a Structurizr DSL file. Path is relative to the selected workspace.
    `workspace` selects a sub-directory under STRUCTURIZR_WORKSPACE_DIR (defaults to
    STRUCTURIZR_DEFAULT_WORKSPACE, then to the base directory).
    """
    return read_dsl_file(path, workspace)


@mcp.tool()
def write_dsl(path: str, content: str, workspace: str | None = None) -> str:
    """
    Write or overwrite a Structurizr DSL file. Path is relative to the selected workspace.
    Creates parent directories as needed. Structurizr will pick up the change automatically
    if it is currently running. `workspace` selects a sub-directory under
    STRUCTURIZR_WORKSPACE_DIR (defaults to STRUCTURIZR_DEFAULT_WORKSPACE, then to the base).
    """
    return write_dsl_file(path, content, workspace)


@mcp.tool()
def list_dsl(directory: str = ".", workspace: str | None = None) -> list[str]:
    """
    List all .dsl files under a directory. Path is relative to the selected workspace.
    Returns paths relative to that workspace. `workspace` selects a sub-directory under
    STRUCTURIZR_WORKSPACE_DIR (defaults to STRUCTURIZR_DEFAULT_WORKSPACE, then to the base).
    """
    return list_dsl_files(directory, workspace)


@mcp.tool()
def validate(path: str, workspace: str | None = None) -> dict:
    """
    Validate a Structurizr DSL file via Docker (structurizr/structurizr validate).
    Returns {valid: bool, errors: [str], output: str}.
    `workspace` selects a sub-directory under STRUCTURIZR_WORKSPACE_DIR (defaults to
    STRUCTURIZR_DEFAULT_WORKSPACE, then to the base directory).
    Requires Docker to be running.
    """
    return validate_workspace(path, workspace)


@mcp.tool()
def export(path: str, format: str = "mermaid", output_dir: str | None = None, workspace: str | None = None) -> dict:
    """
    Export diagrams from a DSL file via Docker.

    Args:
        path: Path to the .dsl file (relative to the selected workspace).
        format: Output format. One of: mermaid (default), plantuml, svg, png,
                json, static, websequencediagrams.
                SVG and PNG capture diagrams exactly as they appear in the Structurizr
                web UI using a Playwright headless browser — requires Structurizr to be
                running at STRUCTURIZR_URL and the playwright Docker image to be available.
                All other formats work without a running server.
        output_dir: Where to write exported files (relative to the selected workspace).
                    Defaults to the same directory as the DSL file.
        workspace: Sub-directory under STRUCTURIZR_WORKSPACE_DIR to target. Defaults to
                   STRUCTURIZR_DEFAULT_WORKSPACE, then to the base directory.

    Returns {files: [str], output: str}.
    Requires Docker to be running.
    """
    return export_diagrams(path, format, output_dir, workspace)


@mcp.tool()
def workspace_json() -> dict:
    """
    Fetch the current workspace model from Structurizr's REST API (GET /api/workspace).
    Returns the full architecture model as JSON: all elements, relationships, and views.
    Requires Structurizr to be running (STRUCTURIZR_URL, default http://localhost:8080).
    """
    return get_workspace_json()


@mcp.tool()
def structurizr_status() -> dict:
    """
    Check whether Structurizr is reachable at the configured URL.
    Returns {reachable: bool, url: str, message: str}.
    """
    return get_structurizr_status()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
