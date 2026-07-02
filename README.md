<div align="center">

<br />

<img src="dashboard/claude_character.svg" width="100" alt="Memex character" />

<h1>Memex</h1>

<p><strong>A self-maintaining wiki workspace for project-based knowledge.</strong></p>

<p>
Drop a source into <code>raw/</code>.<br />
Use Claude to turn it into linked, cited wiki pages.<br />
Browse and operate the result through a dashboard or MCP tools.
</p>

<p>
<a href="#quick-start"><img alt="Quick start" src="https://img.shields.io/badge/quick%20start-5%20min-111?style=flat-square" /></a>
&nbsp;
<img alt="Python" src="https://img.shields.io/badge/python-3.12%2B-111?style=flat-square" />
&nbsp;
<img alt="License" src="https://img.shields.io/badge/license-MIT-111?style=flat-square" />
&nbsp;
<a href="README-ko.md"><img alt="Korean README" src="https://img.shields.io/badge/한국어-README-111?style=flat-square" /></a>
</p>

<br />

<img src="docs/demo.gif" width="100%" alt="Memex dashboard demo" />

</div>

---

## What Memex Is

Memex is an Obsidian-compatible knowledge workspace built around a simple rule:

- sources live in `raw/`
- derived knowledge lives in `wiki/`
- `raw/` is immutable after creation
- every project can have its own schema, history, and maintenance outputs

Instead of re-deriving the same answers from raw documents on every query, Memex keeps a maintained wiki that compounds over time. The repo gives you three connected surfaces:

1. **Dashboard**: web UI and REST API for browsing, ingesting, querying, reviewing, and graph analysis
2. **MCP server**: tool interface for Claude Code, Claude Desktop, Cursor, and other MCP clients
3. **Project workspace layout**: per-project `wiki/`, `raw/`, `CLAUDE.md`, reports, logs, and graph cache

The dashboard and MCP server operate on the same project data, so changes made from either side are immediately visible in the other.

For Codex users, the repository now also includes repo-native instruction surfaces:

- `AGENTS.md` for repository-level guidance
- `.codex/config.toml` to register `CLAUDE.md` as a fallback instruction filename

---

## Architecture At A Glance

```text
                +-----------------------+
                |     MCP clients       |
                | Claude / IDE / SDK    |
                +-----------+-----------+
                            |
                            v
                    mcp-server/memex_mcp.py
                            |
                            v
+---------------------------+---------------------------+
|                    Shared project storage             |
|                                                       |
|  projects/<slug>/ or legacy root                      |
|  ├── raw/              immutable source files         |
|  ├── wiki/             linked markdown knowledge      |
|  ├── CLAUDE.md         per-project schema/rules       |
|  ├── .settings.json    per-project local metadata     |
|  ├── ingest-reports/   ingest reasoning/output        |
|  ├── reflect-reports/  meta-analysis output           |
|  ├── plans/            project planning notes         |
|  └── .graph/           graph cache and labels         |
+---------------------------+---------------------------+
                            ^
                            |
                    dashboard/server.py
                            |
                            v
                Web UI + REST API + graph/universe
```

Key operating constraints:

- `raw/` is append-only and protected from overwrite
- `wiki/` is the writable knowledge surface
- graph and universe views are computed from wiki pages, links, and metadata
- git-backed history enables revert and audit

---

## Feature Modules

### 1. Project System

Memex supports both a legacy single-project layout and a multi-project registry driven by `projects.json`.

- **Legacy mode**: if `projects.json` is missing or empty, the repo root `wiki/` and `raw/` act as the active project
- **Multi-project mode**: each project lives under `projects/<slug>/`
- **Project templates**: new projects can be scaffolded from `templates/`
- **Per-project settings**: schema in `CLAUDE.md`, lightweight local metadata in `.settings.json`, project-specific logs and reports
- **Soft delete**: deleted projects are moved under `projects/.trash/`

### 2. Dashboard

The dashboard is a single Python server with no third-party runtime dependency beyond the standard library for the web layer.

Main views and operations exposed in the UI:

- page tree and page editor
- raw source browser
- ingest
- query
- lint and lint-fix
- reflect
- write
- compare
- review queue
- smart search
- provenance coverage
- ingest history and revert
- graph view
- universe view
- schedules
- AI and CLI settings
- built-in dashboard helper chat

The UI is localized for English, Korean, and Chinese.

### 3. Wiki Maintenance Engine

Memex ships prompt builders and workflows for maintaining the wiki as an accumulated artifact rather than a temporary answer cache.

- **Ingest**: turn a raw source into source summaries, concept/entity pages, links, and an ingest report
- **Lint**: audit missing citations, orphan pages, schema violations, stale pages, and link issues
- **Lint Fix**: apply the common repairs automatically
- **Reflect**: analyze recent ingest/query activity and suggest pages, schema changes, and sources to add
- **Write**: draft cited articles from the current wiki
- **Compare**: compare two pages and save the result
- **Review Refresh**: revisit stale pages
- **Slides**: generate slide output from a page
- **Loop**: run a maintenance sequence such as ingest -> lint -> fix -> reflect -> validate links

### 4. MCP Server

`mcp-server/memex_mcp.py` exposes the workspace through **65 tools** plus resources for instruction and graph summaries.

Tool families:

- project management
- wiki read/write
- raw source operations
- git commit
- semantic wiki operations
- graph analysis
- cross-project universe analysis
- schedule management

Use it when you want Claude or an IDE agent to operate directly on the wiki without going through the dashboard UI.

### 5. Knowledge Graph and Universe

Memex has two graph layers:

- **Project graph**: graph build, stats, community detection, shortest path, neighbors, insights, export
- **Universe graph**: cross-project merged graph, bridge discovery, shortest path across projects, community summaries, content-backed path inspection

Graph cache is stored under each project's `.graph/`. Universe membership and config live under `.memex/`.

### 6. Operations and Deployment

The repo supports:

- local Python run for the dashboard
- Docker Compose for dashboard + MCP + nginx
- local stdio MCP for Claude Code/Desktop
- HTTP MCP for remote deployment behind nginx
- scheduled maintenance jobs

---

## Quick Start

### Local Dashboard

Requirements:

- Python 3.12+
- a browser
- optional: Claude CLI or another configured AI backend for ingest/query/write workflows

Run:

```bash
git clone https://github.com/cmblir/memex.git
cd memex
python dashboard/server.py
```

Open:

- `http://localhost:8090`

You can also use the package entrypoint if installed:

```bash
memex-server
```

### Docker Compose Stack

Create local configuration:

```bash
cp .env.example .env
```

Start everything:

```bash
./deploy.sh deploy
```

Default exposed endpoints from the current compose setup:

- Dashboard through nginx: `http://localhost:3011`
- Direct dashboard container port: `http://localhost:8002`
- MCP HTTP endpoint: `http://localhost:8081/mcp`
- Health check through nginx: `http://localhost:3011/health`

Core deployment commands:

| Command | Purpose |
|---|---|
| `./deploy.sh install` | Create `.env` from `.env.example` |
| `./deploy.sh build` | Build dashboard, MCP, and nginx images |
| `./deploy.sh start` | Start services |
| `./deploy.sh stop` | Stop services |
| `./deploy.sh restart` | Restart services |
| `./deploy.sh status` | Show service status and ports |
| `./deploy.sh logs` | Show logs |
| `./deploy.sh test` | Run HTTP/API health checks |
| `./deploy.sh destroy` | Remove containers and volumes |

---

## Main Workflows

### 1. Create or Select a Project

Use the dashboard header project selector or edit `projects.json`.

Each project gets its own:

- `wiki/`
- `raw/`
- `CLAUDE.md`
- `.settings.json`
- reports, plans, query log, and graph cache

### 2. Add a Source

Put a source into the active project's `raw/` through:

- the dashboard ingest flow
- the raw browser/upload flow
- MCP `add_raw_source`

Important: once a file exists under any `raw/`, Memex treats it as immutable.

### 3. Build Knowledge from the Source

Run ingest. The CLI-driven agent workflow reads the raw source and updates `wiki/` with:

- source summary pages
- concept/entity/analysis pages
- inline citations like `[^src-*]`
- wikilinks between related pages
- an ingest report describing what changed and why

### 4. Query and Review the Wiki

Use:

- **Query** for grounded question answering
- **Search** for TF-IDF full-text retrieval
- **Review** for stale page refresh
- **History** to inspect ingest commits and revert when necessary
- **Provenance** to inspect citation coverage

### 5. Maintain the Knowledge Base

Run:

- **Lint** to find gaps and inconsistencies
- **Lint Fix** to auto-repair common issues
- **Reflect** for higher-level maintenance suggestions
- **Loop** for periodic multi-step maintenance
- **Schedules** for recurring automation

### 6. Explore Structure with Graphs

Use:

- **Graph** to inspect one project's knowledge structure
- **Universe** to inspect cross-project connections, merged nodes, and bridges

---

## MCP Usage

Memex supports two MCP transports.

### Local `stdio` MCP

Best for local Claude Code or Claude Desktop usage.

Install:

```bash
bash mcp-server/install.sh
```

Register with Claude Code:

```bash
claude mcp add --scope user memex \
  -- "$PWD/mcp-server/.venv/bin/python" "$PWD/mcp-server/memex_mcp.py"
```

### Remote HTTP MCP

Best for remote deployment, IDE access, or shared environments.

Run with Docker Compose or directly with:

```bash
MEMEX_MCP_TRANSPORT=http MEMEX_MCP_PORT=8081 python3 mcp-server/memex_mcp.py
```

HTTP endpoint:

- `POST /mcp`

For deeper setup examples and client configs, see:

- [`mcp-server/README.md`](mcp-server/README.md)
- [`docs/mcp-configuration.md`](docs/mcp-configuration.md)
- [`docs/mcp-server-deployment.md`](docs/mcp-server-deployment.md)

---

## Configuration

Primary environment variables from `.env.example`:

| Variable | Purpose | Default |
|---|---|---|
| `MEMEX_PORT` | nginx external port | `3011` |
| `MEMEX_DASHBOARD_PORT` | internal dashboard port | `8000` |
| `MEMEX_DASHBOARD_EXPOSED_PORT` | direct dashboard host port | `8002` |
| `MEMEX_MCP_PORT` | MCP HTTP port | `8081` |
| `MEMEX_MCP_TRANSPORT` | MCP mode: `stdio` or `http` | `stdio` |
| `MEMEX_ACTIVE_PROJECT` | active project slug override | empty |
| `MEMEX_GIT_AUTO_COMMIT` | auto-commit behavior | `true` |
| `MEMEX_CLI_TYPE` | CLI backend type | unset |
| `MEMEX_CLI_BINARY` | CLI executable | unset |
| `MEMEX_CLAUDE_TIMEOUT` | long-running CLI timeout | `600` |
| `MEMEX_TZ` | container timezone | `Asia/Shanghai` |

The dashboard persists runtime CLI settings in `.dashboard-settings.json`. Project-local `.settings.json` files remain available for lightweight metadata, but no longer carry runtime backend selection.

---

## Repository Layout

```text
dashboard/         Web UI, REST API, graph/universe logic, scheduler
mcp-server/        MCP entrypoint, install script, MCP-specific docs
templates/         Project templates and starter CLAUDE.md files
docs/              Deployment and MCP configuration guides
tests/             Regression tests for dashboard/wiki/raw behavior
wiki/              Legacy root wiki data
raw/               Legacy root raw sources
projects.json      Project registry
.memex/            Universe configuration and shared metadata
AGENTS.md          Repository-level Codex instructions
.codex/            Project-scoped Codex configuration
```

Other important directories created per project:

```text
projects/<slug>/wiki/
projects/<slug>/raw/
projects/<slug>/ingest-reports/
projects/<slug>/reflect-reports/
projects/<slug>/plans/
projects/<slug>/.graph/
```

---

## API and Integration Notes

- The dashboard serves HTML and REST endpoints from `dashboard/server.py`
- Graph tools in MCP HTTP mode call back into the dashboard API
- Writes are shared across dashboard and MCP surfaces on the same filesystem
- `raw/` protections are enforced in both dashboard and MCP code paths
- Current regression tests cover wiki graph generation and raw path safety
- Codex reads `AGENTS.md` first and uses `.codex/config.toml` to treat nested `CLAUDE.md` files as fallback project instructions

If you are extending the repo, start from:

- [`dashboard/server.py`](dashboard/server.py)
- [`dashboard/project_registry.py`](dashboard/project_registry.py)
- [`dashboard/wiki_ops.py`](dashboard/wiki_ops.py)
- [`mcp-server/memex_mcp.py`](mcp-server/memex_mcp.py)

---

## Further Docs

- [`mcp-server/README.md`](mcp-server/README.md)
- [`docs/mcp-configuration.md`](docs/mcp-configuration.md)
- [`docs/mcp-server-deployment.md`](docs/mcp-server-deployment.md)
- [`raw/pkms-system-design.md`](raw/pkms-system-design.md)
- [`wiki/overview.md`](wiki/overview.md)

---

## License

MIT.
