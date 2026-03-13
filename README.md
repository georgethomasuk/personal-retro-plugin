# personal-retro

A Claude Code plugin that runs a personal retrospective. It extracts your Claude Code session logs and generates coaching notes with themes, patterns, friction points, and probing questions.

## Install

### From the marketplace

If the marketplace is configured:

```
/plugin install personal-retro@georgethomas-marketplace
```

### From GitHub directly

```
/plugin install github:georgethomasuk/personal-retro-plugin
```

### Local development

```bash
claude --plugin-dir /path/to/personal-retro-plugin
```

## Usage

```
/personal-retro:personal-retro        # Retro on the last 7 days
/personal-retro:personal-retro 14     # Retro on the last 14 days
```

The plugin will:

1. Extract your prompts from `~/.claude/projects/` for the specified period
2. Present initial observations and ask probing questions
3. Have a back-and-forth coaching conversation with you
4. Write retro notes only when you're ready

## Standalone script

The extraction script can also be used independently:

```bash
# JSON output to stdout
python3 skills/personal-retro/extract_sessions.py --days 7

# Markdown output to stdout
python3 skills/personal-retro/extract_sessions.py --days 7 --format markdown

# Write to a specific file
python3 skills/personal-retro/extract_sessions.py --days 14 --format markdown --output notes.md

# Auto-named output in a directory
python3 skills/personal-retro/extract_sessions.py --days 7 --format markdown --output-dir ./personal-retro-notes
```

## What the coach does

The retro coach is not a summariser. It's a curious, supportive, but challenging coach that:

- Notices patterns you might not see yourself
- Asks probing questions that make you think
- Gently challenges areas where you seem stuck
- Reflects back themes with specific evidence from your sessions
- Identifies what you might be avoiding

The coach presents observations first, then has a conversation with you before writing anything. The discussion is the point — the notes capture what you arrived at together.

## Output structure

Each retro notes file includes:

- **Themes I noticed** — recurring topics with quoted evidence
- **Decisions in motion** — what got resolved vs. what's still open
- **Friction points** — where you got stuck or frustrated
- **What you might be avoiding** — gaps and dropped threads
- **Momentum check** — what's moving forward vs. stuck
- **One question to sit with** — a powerful question for the week ahead

## License

MIT
