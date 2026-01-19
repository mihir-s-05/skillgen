# SkillGen

An MCP server that lets LLMs install documentation skills from any `llms.txt` URL.

Give an LLM the URL to an `llms.txt` file, and it will fetch the documentation, generate a skill bundle, and install it for immediate use.

## Quick Start (MCP Server)

### Install

```bash
pip install skillgen
```

### Add to Claude Code

Add to your Claude Code MCP settings (`~/.claude/claude_desktop_config.json` or via `claude mcp add`):

```json
{
  "mcpServers": {
    "skillgen": {
      "command": "skillgen-mcp"
    }
  }
}
```

Or use the CLI:

```bash
claude mcp add skillgen skillgen-mcp
```

### Use It

Once configured, just ask Claude to install a skill:

> "Install the skill from https://docs.stripe.com/llms.txt"

The LLM will call `install_skill_from_url` with the URL, and the skill will be installed to `~/.claude/skills/` for immediate use.

## Available Tools

### `install_skill_from_url`

Install a skill from an llms.txt URL.

**Parameters:**
- `url` (required): URL to an llms.txt file or documentation site
- `name` (optional): Override the skill name
- `include_optional` (optional): Include optional documentation sections (default: false)
- `snapshot` (optional): Download and cache documentation (default: true)

**Example:**
```
Install the Anthropic API skill from https://docs.anthropic.com/llms.txt
```

### `list_installed_skills`

List all skills currently installed in Claude Code.

**Example:**
```
What skills do I have installed?
```

## What is llms.txt?

[llms.txt](https://llmstxt.org/) is a standard format for providing LLM-friendly documentation. It's a simple markdown file that lists documentation links in a structured way:

```markdown
# Project Name
> Brief description

## Getting Started
- [Quick Start](https://example.com/docs/quickstart): Get up and running

## API Reference
- [Authentication](https://example.com/docs/auth): API authentication
- [Endpoints](https://example.com/docs/endpoints): Available endpoints
```

Many documentation sites now provide llms.txt files. Check if your favorite tool has one at `https://example.com/llms.txt`.

## CLI Usage

SkillGen also works as a standalone CLI:

```bash
# Generate and install a skill
skillgen https://docs.example.com/llms.txt --target claude

# Generate without installing
skillgen https://docs.example.com/llms.txt --out ./skills
```

### CLI Flags

- `--target codex|claude|opencode|amp|roo|cursor` - Install target
- `--include-optional` - Include the Optional section
- `--no-snapshot` - Generate link-only references (no doc download)
- `--allow-external` - Allow external domains
- `--by-link` - One file per link (default is by section)

## Development

```bash
pip install -e .[test]
pytest
```

## License

MIT
