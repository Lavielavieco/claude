# CLAUDE.md

## Project Overview

This is the **claude** repository, currently in its initial setup phase. The project has been freshly initialized and does not yet contain application source code, build tooling, or dependency configuration.

**Repository**: `Lavielavieco/claude`
**Default branch**: `main`

## Repository Structure

```
.
├── CLAUDE.md          # AI assistant guidelines (this file)
└── README.md          # Project README
```

As the project grows, this section should be updated to reflect new directories and files.

## Development Setup

No build system, package manager, or runtime dependencies are configured yet. When they are added, document the setup steps here:

1. **Prerequisites**: (list required tools, runtimes, versions)
2. **Install dependencies**: (e.g., `npm install`, `pip install -r requirements.txt`)
3. **Environment variables**: see [Environment Variables & API Keys](#environment-variables--api-keys)
4. **Run the project**: (e.g., `npm run dev`, `python main.py`)

## Environment Variables & API Keys

The following API keys are used across projects in this account. **Never commit the actual key values to this repo.**

| Variable | Service | Where to get a key |
|----------|---------|--------------------|
| `UNUSUAL_WHALES_API_KEY` | Unusual Whales (options flow data) | https://unusualwhales.com |
| `EODHD_API_KEY` | EODHD (historical stock/financial data) | https://eodhd.com |
| `MASSIVE_API_KEY` | Massive.com | https://massive.com |

### Configuring keys for Claude Code sessions

There are two layers, both required for full coverage:

**1. Local Claude Code config (`~/.claude/settings.json`)**

Adds the keys as `env` entries so they are exported into every Claude Code session on this user account. Already configured for the current container, but this file lives **inside the ephemeral container** and is destroyed when the container is recycled.

**2. Claude Code on the Web — Environment Variables (persistent)**

To survive container recycles, the same keys must be set at the environment level:

1. Go to https://claude.ai/code
2. Open the environment used for this repo (or the default environment)
3. **Settings → Environment variables**
4. Add each variable name + value (`UNUSUAL_WHALES_API_KEY`, `EODHD_API_KEY`, `MASSIVE_API_KEY`)
5. Save — new sessions will have them injected automatically

### Network access (sandbox allowed domains)

The following domains are whitelisted in `~/.claude/settings.json` under `sandbox.network.allowedDomains` and in `permissions.allow` via `WebFetch(domain:...)`:

- `unusualwhales.com` (and subdomains)
- `eodhd.com` (and subdomains)
- `massive.com` (and subdomains)

If the environment's outbound network policy is restrictive, these domains must also be allowlisted in the environment's network policy via the claude.ai/code dashboard.

## Common Commands

No scripts or commands are defined yet. Update this section as tooling is added:

| Command | Description |
|---------|-------------|
| _TBD_   | _TBD_       |

## Testing

No test framework is configured. When tests are added, document:

- **Test framework**: (e.g., Jest, pytest, Go test)
- **Run all tests**: (command)
- **Run a single test**: (command)
- **Test file naming convention**: (e.g., `*.test.ts`, `test_*.py`)
- **Test location**: (e.g., colocated with source, separate `tests/` directory)

## Code Style and Conventions

No linter or formatter is configured yet. When established, document:

- **Linter**: (e.g., ESLint, Ruff, golangci-lint)
- **Formatter**: (e.g., Prettier, Black, gofmt)
- **Style guide**: (link or description)
- **Naming conventions**: (e.g., camelCase for variables, PascalCase for components)

## Git Workflow

- **Branch naming**: Feature branches use the `claude/` prefix when created by AI assistants
- **Commit messages**: Use clear, descriptive messages that explain _why_, not just _what_
- **Default branch**: `main`

## Architecture Decisions

No architecture decisions have been recorded yet. As the project takes shape, document key decisions here using the format:

- **Decision**: (what was decided)
- **Context**: (why it was needed)
- **Rationale**: (why this option was chosen)

## Guidelines for AI Assistants

- Read existing code before proposing changes
- Do not over-engineer; keep solutions minimal and focused
- Do not add features, refactoring, or improvements beyond what was requested
- Prefer editing existing files over creating new ones
- Avoid introducing security vulnerabilities (OWASP Top 10)
- Keep this CLAUDE.md file updated as the project evolves
