# structurizr-mcp

An MCP server that lets Claude read, write, validate, and export [Structurizr](https://structurizr.com) architecture models. Works with the [Structurizr local tool](https://docs.structurizr.com/local) (`structurizr/structurizr`) — the successor to Structurizr Lite.

> **Note:** Structurizr Lite (`structurizr/lite`) was discontinued in early 2026. The replacement is the unified `structurizr/structurizr` Docker image run in `local` mode. The DSL is unchanged.

**The only runtime dependency is Docker.** Validate and most export formats run via `structurizr/structurizr`. SVG/PNG export additionally uses `mcr.microsoft.com/playwright` to capture diagrams exactly as they appear in the Structurizr web UI — both images are pulled automatically on first use.

## What it does

| Tool | Description |
|---|---|
| `read_dsl` | Read a `.dsl` workspace file |
| `write_dsl` | Create or update a `.dsl` file |
| `list_dsl` | List `.dsl` files in a directory |
| `validate` | Validate a DSL file via Docker |
| `export` | Export diagrams to Mermaid, SVG, PNG, PlantUML, JSON |
| `workspace_json` | Fetch the full architecture model from the Structurizr REST API |
| `structurizr_status` | Check if Structurizr is running |

## Prerequisites

### 1. Docker

Both the Structurizr viewer and the validate/export tools run via Docker. No other tools need to be installed.

Start Structurizr pointing at your architecture directory:

```bash
docker run -it --rm -p 8080:8080 \
  -v $PWD/<project-name>:/usr/local/structurizr \
  structurizr/structurizr local
```

Open http://localhost:8080 in your browser to view diagrams.

> **SVG and PNG exports** require Structurizr to be running and use a Playwright headless browser (`mcr.microsoft.com/playwright`) to capture diagrams exactly as they appear in the web UI. All other export formats (Mermaid, PlantUML, JSON, etc.) work without a running server.

### 2. uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

```bash
git clone https://github.com/ksgit/structurizr-mcp
cd structurizr-mcp
```

No separate install step — `uv` handles the Python environment automatically on first run.

## Connecting to Claude Code

Add to your project's `.claude/settings.json` (or your global `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "structurizr": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/structurizr-mcp", "structurizr-mcp"],
      "env": {
        "STRUCTURIZR_WORKSPACE_DIR": "./architecture"
      }
    }
  }
}
```

Replace `/path/to/structurizr-mcp` with the actual path where you cloned this repo,
and `./architecture` with the path to your Structurizr data directory (the same directory
you mount into Docker with `-v`).

Or use the CLI shortcut:

```bash
claude mcp add structurizr -- uv run --directory /path/to/structurizr-mcp structurizr-mcp
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|---|---|---|
| `STRUCTURIZR_WORKSPACE_DIR` | `.` | Base directory that bounds all file access (the sandbox root) |
| `STRUCTURIZR_DEFAULT_WORKSPACE` | _(none)_ | Sub-directory under the base used when a tool call omits `workspace` |
| `STRUCTURIZR_URL` | `http://localhost:8080` | Structurizr base URL (used for SVG/PNG export and API tools) |
| `STRUCTURIZR_WORKSPACE_ID` | `1` | Workspace ID (local mode always uses `1`) |
| `STRUCTURIZR_API_KEY` | _(none)_ | API key for HMAC authentication (optional in local mode) |
| `STRUCTURIZR_API_SECRET` | _(none)_ | API secret for HMAC authentication (optional in local mode) |

Authentication is only required if you have configured API credentials in Structurizr. For local mode with no credentials configured, leave `STRUCTURIZR_API_KEY` and `STRUCTURIZR_API_SECRET` unset.

### Multiple workspaces

When several Structurizr workspaces live side by side (e.g. `repo/projectA/workspace.dsl` and
`repo/projectB/workspace.dsl`), point `STRUCTURIZR_WORKSPACE_DIR` at their **common parent** and
select one per call with the `workspace` argument that `read_dsl`, `write_dsl`, `list_dsl`,
`validate`, and `export` all accept:

```jsonc
"env": {
  "STRUCTURIZR_WORKSPACE_DIR": "/path/to/repo",
  "STRUCTURIZR_DEFAULT_WORKSPACE": "projectA"   // used when `workspace` is omitted
}
```

- `validate(path="workspace.dsl")` → validates `projectA/workspace.dsl` (the default)
- `validate(path="workspace.dsl", workspace="projectB")` → validates `projectB/workspace.dsl`
- `export(path="workspace.dsl", format="svg", output_dir="diagrams/svg", workspace="projectB")`
  writes into `projectB/diagrams/svg/`

`path`, `output_dir`, and `workspace` are all resolved under the base and may not escape it.
For SVG/PNG, the running `structurizr local` container must be serving the same workspace you
target (its `-v` mount selects which workspace the web UI renders).

## Example usage

Once connected, you can ask Claude things like:

- "Read the current workspace.dsl and explain the architecture"
- "Add a new microservice called PaymentService to the architecture"
- "Export all diagrams as SVG and save them to diagrams/svg/"
- "Validate the workspace and fix any errors"
- "What containers exist in the current workspace?"

## License

MIT
