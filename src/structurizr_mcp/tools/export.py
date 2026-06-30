import json
import subprocess
from pathlib import Path
from structurizr_mcp.config import config
from structurizr_mcp.tools.dsl import _resolve

DOCKER_IMAGE = "structurizr/structurizr"
PLAYWRIGHT_IMAGE = "mcr.microsoft.com/playwright:v1.44.0-jammy"
CONTAINER_WORKSPACE = "/usr/local/structurizr"

# Formats exported purely from the DSL — no running Structurizr server needed.
CLI_ONLY_FORMATS = ("mermaid", "plantuml", "json", "static", "websequencediagrams")
# Formats rendered by the Structurizr web UI via a headless browser — require a running server.
SERVER_FORMATS = ("svg", "png")

SUPPORTED_FORMATS = CLI_ONLY_FORMATS + SERVER_FORMATS

_EXTENSION_MAP = {
    "mermaid": ".md",
    "plantuml": ".puml",
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


def _get_view_keys() -> list[str]:
    """Fetch all view keys from the running Structurizr workspace."""
    from structurizr_mcp.tools.api import get_workspace_json
    workspace = get_workspace_json()
    views_section = workspace.get("views", {})
    keys = []
    for view_type in (
        "systemLandscapeViews",
        "systemContextViews",
        "containerViews",
        "componentViews",
        "dynamicViews",
        "deploymentViews",
        "filteredViews",
        "customViews",
    ):
        for view in views_section.get(view_type, []):
            key = view.get("key")
            if key:
                keys.append(key)
    return keys


def _export_svg_via_browser(
    view_keys: list[str],
    out_resolved: Path,
    workspace_dir: Path,
    structurizr_url: str,
    fmt: str = "svg",
) -> dict:
    """
    Export diagrams as SVG using a Playwright headless browser pointed at the
    running Structurizr server. Captures diagrams exactly as they appear in the
    Structurizr web UI.
    """
    # Parse port from structurizr_url (default 8080)
    import urllib.parse as _urlparse
    parsed = _urlparse.urlparse(structurizr_url)
    remote_host = parsed.hostname or "localhost"
    remote_port = parsed.port or 8080
    # Convert localhost → host.docker.internal for the proxy target (container → host)
    docker_host = remote_host.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")

    container_out = _container_path(out_resolved, workspace_dir)
    ext = ".svg" if fmt == "svg" else ".png"

    tmp_dir = workspace_dir / ".playwright-tmp"
    tmp_dir.mkdir(exist_ok=True)
    script_path = tmp_dir / "export-diagrams.js"

    script = f"""
const {{ chromium }} = require('playwright');
const net = require('net');
const fs = require('fs');
const path = require('path');

const views = {json.dumps(view_keys)};
const outputDir = '{container_out}';
// Structurizr validates the Host header and rejects 'host.docker.internal'.
// We create a TCP proxy inside the container: localhost:{remote_port} → {docker_host}:{remote_port}
// Playwright connects to localhost, so the Host header is 'localhost:{remote_port}' which Structurizr accepts.
const PROXY_PORT = {remote_port};
const REMOTE_HOST = '{docker_host}';
const REMOTE_PORT = {remote_port};
const baseUrl = 'http://localhost:' + PROXY_PORT;

const proxyServer = net.createServer(socket => {{
  const remote = net.connect(REMOTE_PORT, REMOTE_HOST);
  socket.pipe(remote);
  remote.pipe(socket);
  socket.on('error', () => remote.destroy());
  remote.on('error', () => socket.destroy());
}});

(async () => {{
  await new Promise(resolve => proxyServer.listen(PROXY_PORT, '127.0.0.1', resolve));
  console.log('Proxy listening on localhost:' + PROXY_PORT + ' → ' + REMOTE_HOST + ':' + REMOTE_PORT);

  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];

  for (const viewKey of views) {{
    try {{
      const url = baseUrl + '/workspace/1/diagrams#' + encodeURIComponent(viewKey);
      console.log('Exporting: ' + viewKey);
      await page.goto(url, {{ waitUntil: 'networkidle', timeout: 30000 }});

      // Wait until Structurizr has loaded and the export function is available
      await page.waitForFunction(
        () => typeof structurizr !== 'undefined' &&
              structurizr.diagram &&
              typeof structurizr.diagram.exportCurrentDiagramToSVG === 'function',
        {{ timeout: 30000 }}
      );
      // Extra settle time for layout engine to finish
      await page.waitForTimeout(1500);

      const svgMarkup = await page.evaluate(
        () => structurizr.diagram.exportCurrentDiagramToSVG({{}}).markup
      );

      const outFile = path.join(outputDir, 'structurizr-' + viewKey + '{ext}');
      fs.writeFileSync(outFile, svgMarkup);
      console.log('Written: ' + outFile);
    }} catch (err) {{
      errors.push(viewKey + ': ' + err.message);
      console.error('Failed ' + viewKey + ': ' + err.message);
    }}
  }}

  await browser.close();
  proxyServer.close();
  if (errors.length > 0) {{
    process.stderr.write('Errors: ' + errors.join(', ') + '\\n');
    process.exit(1);
  }}
}})();
"""

    # package.json lets npm install playwright and caches node_modules in the workspace
    # dir (which is a Docker volume), so only the first run is slow.
    pkg_json = tmp_dir / "package.json"
    pkg_json.write_text(json.dumps({
        "name": "playwright-export",
        "version": "1.0.0",
        "dependencies": {"playwright": "1.44.0"},
    }))
    script_path.write_text(script)

    container_tmp = _container_path(tmp_dir, workspace_dir)
    container_script = _container_path(script_path, workspace_dir)

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--add-host=host.docker.internal:host-gateway",
                "-v", f"{workspace_dir}:{CONTAINER_WORKSPACE}",
                "-e", "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
                PLAYWRIGHT_IMAGE,
                "bash", "-c",
                f"cd {container_tmp} && npm install --prefer-offline --silent 2>/dev/null && node {container_script}",
            ],
            capture_output=True,
            text=True,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            raise RuntimeError(f"Playwright SVG export failed:\n{output}")
    finally:
        script_path.unlink(missing_ok=True)
        pkg_json.unlink(missing_ok=True)

    files = [str(p) for p in sorted(out_resolved.glob(f"*{ext}"))]
    return {"files": files, "output": output}


def export_diagrams(path: str, format: str = "mermaid", output_dir: str | None = None, workspace: str | None = None) -> dict:
    """
    Export diagrams from a Structurizr DSL file.

    CLI formats (mermaid, plantuml, json, static, websequencediagrams) use
    Docker (structurizr/structurizr export) and work without a running server.

    SVG and PNG use a Playwright headless browser (mcr.microsoft.com/playwright)
    that connects to the running Structurizr server and captures diagrams exactly
    as they appear in the web UI. Both Docker images must be available.

    Args:
        path: Path to the .dsl file (relative to the selected workspace).
        format: Output format — mermaid (default), plantuml, svg, png,
                json, static, websequencediagrams.
        output_dir: Where to write exported files (relative to the selected workspace).
                    Defaults to the same directory as the DSL file.
        workspace: Sub-directory under STRUCTURIZR_WORKSPACE_DIR to target. Defaults to
                   STRUCTURIZR_DEFAULT_WORKSPACE, then to the base directory.

    Returns a dict with 'files' (list of output paths) and 'output' (raw CLI output).
    """
    fmt = format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{format}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")

    workspace_dir = config.effective_workspace_dir(workspace)
    resolved = _resolve(path, workspace)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    if output_dir is None:
        out_resolved = resolved.parent
    else:
        out_resolved = _resolve(output_dir, workspace)
        out_resolved.mkdir(parents=True, exist_ok=True)

    if fmt in SERVER_FORMATS:
        view_keys = _get_view_keys()
        return _export_svg_via_browser(view_keys, out_resolved, workspace_dir, config.structurizr_url, fmt)

    # CLI-only formats: use structurizr/structurizr export
    cmd = [
        "docker", "run", "--rm",
        "--add-host=host.docker.internal:host-gateway",
        "-v", f"{workspace_dir}:{CONTAINER_WORKSPACE}",
        DOCKER_IMAGE, "export",
        "-w", _container_path(resolved, workspace_dir),
        "-f", fmt,
        "-o", _container_path(out_resolved, workspace_dir),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        raise RuntimeError(f"Structurizr export failed:\n{output}")

    ext = _EXTENSION_MAP.get(fmt, f".{fmt}")
    files = [str(p) for p in sorted(out_resolved.glob(f"*{ext}"))]

    return {"files": files, "output": output}
