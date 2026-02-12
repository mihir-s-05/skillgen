# SkillGen
Turn any `llms.txt` into a ready-to-use Agent Skill.

SkillGen reads the curated links in `llms.txt`, optionally snapshots the content into `references/`, and generates a clean `SKILL.md` plus indexes and provenance metadata. It installs skills to `~/.agents/skills` by default (or `~/.claude/skills` with `--claude`).

## Quick start
```bash
pip install skillgen
# or for local development
pip install -e .
skillgen https://docs.example.com/llms.txt --out ./skills
```

## What you get
- `SKILL.md` with a concise description and trigger keywords
- `references/INDEX.md` and section indexes
- `references/catalog.json` and provenance files
- `manifest.json` for auditability

## Keyword generation
By default SkillGen uses deterministic heuristic keyword/description generation for fast, stable output.

Heuristic levels:
- `compact`: shortest description
- `balanced` (default): medium detail
- `verbose`: most detailed description with extra navigation cues

Heuristic level affects the `description` narrative in `SKILL.md` only. Keyword extraction stays stable across levels.

## Common flags
- `--name` override skill name
- `--include-optional` include Optional section links
- `--no-snapshot` generate link-only references
- `--allow-external` allow external domains
- `--heuristic-level compact|balanced|verbose`
- `--claude` install to `~/.claude/skills` instead of default path

## Install paths
- default: `~/.agents/skills`
- with `--claude`: `~/.claude/skills`

## Development
```bash
pip install -e .[test]
pytest
```
