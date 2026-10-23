# AGENTS.md

## Project Overview

Lerd Service Store — the community-driven collection of service presets that
powers Lerd. Each preset lives under `services/` and conforms to the schema in
`schema/`. See `README.md` for the contribution format.

### Verification

Validate every new or edited preset against `schema/` before opening a change.

## Agent setup

Used with four coding agents: OpenCode, Codex, Cursor, and Claude Code.
`AGENTS.md` is the shared instruction source for all of them. Where a project
generates `CLAUDE.md`/`AGENTS.md` from another source, follow that project's
generator instead of editing the generated file. Keep this file accurate — the
agents trust it.

- **Skills**: managed centrally with `skills-manager-cli` (library at
  `~/.skills-manager/skills`). Where a project keeps per-agent skill trees
  (`.opencode/skills`, `.codex/skills`, `.claude/skills`, `.cursor/skills`,
  `.agents/skills`) they are normally machine-local symlinks into the library and
  git-ignored. If the project generates them (for example sibylhub's mirrored
  `openspec-*` skills), edit the generator source, not the copies.
- **MCP**: keep only project-local servers in project config. Shared tools come
  from the MCPJungle gateway groups (`coding`, `research`, `browser`, `design`,
  `workspace`) at `http://127.0.0.1:8741/v0/groups/<group>/mcp`; do not register a
  duplicate copy of an upstream server in a host config.
- **Planning**: OpenSpec (`openspec/`) is authoritative for planned changes; use
  `openspec` to propose and validate, and `openspec-auto` to run batches.
