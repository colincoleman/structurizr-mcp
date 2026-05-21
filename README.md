# structurizr-mcp

An MCP server that lets Claude read, write, validate, and export [Structurizr](https://structurizr.com) architecture models. Works with the [Structurizr local tool](https://docs.structurizr.com/local) (`structurizr/structurizr`) — the successor to Structurizr Lite.

> **Note:** Structurizr Lite (`structurizr/lite`) was discontinued in early 2026. The replacement is the unified `structurizr/structurizr` Docker image run in `local` mode. The DSL is unchanged.

## What it does

| Tool | Description |
|---|---|
| `read_dsl` | Read a `.dsl` workspace file |
| `write_dsl` | Create or update a `.dsl` file |
| `list_dsl` | List `.dsl` files in a directory |
| `validate` | Validate a DSL file using `structurizr-cli` |
| `export` | Export diagrams to Mermaid, SVG, PNG, PlantUML |
| `workspace_json` | Fetch the full architecture model from the Structurizr REST API |
| `structurizr_status` | Check if Structurizr is running |

## Prerequisites

### 1. Docker (for the Structurizr local tool)

Start Structurizr pointing at your architecture directory:

```bash
docker run -it --rm -p 8080:8080 \
  -v $PWD/<project-name>:/usr/local/structurizr \
  structurizr/structurizr local
```

Open http://localhost:8080 in your browser to view diagrams.

### 2. structurizr-cli (for validate and export)

Download the CLI from the [Structurizr CLI releases](https://github.com/structurizr/cli/releases) and place it on your `PATH`, or set `STRUCTURIZR_CLI` to the full path.

### 3. uv

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
| `STRUCTURIZR_WORKSPACE_DIR` | `.` | Directory containing `.dsl` files |
| `STRUCTURIZR_URL` | `http://localhost:8080` | Structurizr base URL |
| `STRUCTURIZR_WORKSPACE_ID` | `1` | Workspace ID (local mode always uses `1`) |
| `STRUCTURIZR_API_KEY` | _(none)_ | API key for HMAC authentication (optional in local mode) |
| `STRUCTURIZR_API_SECRET` | _(none)_ | API secret for HMAC authentication (optional in local mode) |
| `STRUCTURIZR_CLI` | `structurizr-cli` | Path to the structurizr-cli binary |

Authentication is only required if you have configured API credentials in Structurizr. For local mode with no credentials configured, leave `STRUCTURIZR_API_KEY` and `STRUCTURIZR_API_SECRET` unset.

## Example usage

Once connected, you can ask Claude things like:

- "Read the current workspace.dsl and explain the architecture"
- "Add a new microservice called PaymentService to the architecture"
- "Export all diagrams as Mermaid so I can add them to the docs"
- "Validate the workspace and fix any errors"
- "What containers exist in the current workspace?"

## License

MIT
