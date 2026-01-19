# AutoSkill
Turn any `llms.txt` into a ready-to-use Agent Skill.

AutoSkill reads the curated links in `llms.txt`, optionally snapshots the content into `references/`, and generates a clean `SKILL.md` plus indexes and provenance metadata. It can also install the skill into common tool locations (Codex, Claude Code, OpenCode, Amp, Roo, Cursor).

## Quick start
```bash
pip install -e .
autoskill https://docs.example.com/llms.txt --out ./skills
```

## What you get
- `SKILL.md` with a concise description and trigger keywords
- `references/INDEX.md` and section indexes
- `references/catalog.json` and provenance files
- `manifest.json` for auditability

## LLM keyword generation
By default AutoSkill uses a local Transformers model to generate the description and keywords. If the model is not available, it falls back to deterministic heuristics (unless you pass `--no-llm-fallback`).

Recommended model: `Qwen/Qwen3-0.6B`.

```bash
pip install -e .[llm]
autoskill https://docs.example.com/llms.txt --llm-model Qwen/Qwen3-0.6B
```

## Common flags
- `--include-optional` include the Optional section
- `--no-snapshot` generate link-only references
- `--allow-external` allow external domains
- `--by-link` one file per link (default is by section)
- `--keyword-mode heuristic|llm|auto`
- `--target codex|claude|opencode|amp|roo|cursor`
- `--scope user|project` (default is user/global where supported)

## Install targets
- codex: `~/.codex/skills` (user/global) or `./.codex/skills`
- claude: `~/.claude/skills` (user/global) or `./.claude/skills`
- opencode: `~/.config/opencode/skill` (user/global) or `./.opencode/skill` (uses `skills/` if present)
- amp: `~/.config/agents/skills` (user/global) or `./.agents/skills`
- roo: `~/.roo/skills` (user/global) or `./.roo/skills` (or `skills-<mode>`)
- cursor: project only `./.cursor/rules` (creates a `.mdc` rule)

## Development
```bash
pip install -e .[test]
pytest
```
