#!/usr/bin/env python3
"""
Extract Claude Code sessions for personal retrospectives.

Parses JSONL session files from ~/.claude/projects/ and outputs
structured data for coaching analysis.

Usage:
    python extract_sessions.py [--days 7] [--format json|markdown] [--output PATH] [--output-dir DIR]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict


def find_sessions(projects_dir: Path, days_back: int = 7) -> list[dict]:
    """Find all session files with messages from the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    sessions = []

    if not projects_dir.exists():
        print(f"Warning: Claude projects directory not found at {projects_dir}")
        return sessions

    for session_file in projects_dir.rglob("*.jsonl"):
        session_messages = []
        session_meta = {
            "file": str(session_file),
            "project": decode_project_path(session_file.parent.name),
        }

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line)
                        msg_time = parse_timestamp(msg.get("timestamp", ""))
                        if msg_time and msg_time > cutoff:
                            session_messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except (IOError, OSError) as e:
            print(f"Warning: Could not read {session_file}: {e}")
            continue

        if session_messages:
            sessions.append(
                {
                    **session_meta,
                    "messages": session_messages,
                    "first_message": min(
                        m.get("timestamp", "") for m in session_messages
                    ),
                    "last_message": max(
                        m.get("timestamp", "") for m in session_messages
                    ),
                }
            )

    return sessions


def decode_project_path(encoded: str) -> str:
    """Decode the URL-encoded project path from directory name."""
    if encoded.startswith("-"):
        return encoded.replace("-", "/", 1).replace("-", "/")
    return encoded


def parse_timestamp(ts: str) -> datetime | None:
    """Parse ISO timestamp string to datetime."""
    if not ts:
        return None
    try:
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def extract_user_prompts(sessions: list[dict]) -> list[dict]:
    """Extract just user prompts with metadata for analysis."""
    prompts = []

    for session in sessions:
        for msg in session.get("messages", []):
            if msg.get("type") != "user":
                continue

            content = msg.get("message", {}).get("content", [])
            text_content = extract_text_content(content)

            if text_content:
                prompts.append(
                    {
                        "timestamp": msg.get("timestamp", ""),
                        "date": format_date(msg.get("timestamp", "")),
                        "project": session.get("project", ""),
                        "content": text_content,
                        "session_file": session.get("file", ""),
                    }
                )

    prompts.sort(key=lambda x: x["timestamp"])
    return prompts


def extract_text_content(content) -> str:
    """Extract text from message content (handles various formats)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts)
    return ""


def format_date(ts: str) -> str:
    """Format timestamp as readable date."""
    dt = parse_timestamp(ts)
    if dt:
        return dt.strftime("%b %d, %H:%M")
    return ""


def group_by_day(prompts: list[dict]) -> dict[str, list[dict]]:
    """Group prompts by day for daily summaries."""
    by_day = defaultdict(list)
    for prompt in prompts:
        dt = parse_timestamp(prompt["timestamp"])
        if dt:
            day = dt.strftime("%Y-%m-%d")
            by_day[day].append(prompt)
    return dict(by_day)


def generate_summary(prompts: list[dict]) -> dict:
    """Generate summary statistics."""
    projects = set(p["project"] for p in prompts)
    by_day = group_by_day(prompts)

    return {
        "total_prompts": len(prompts),
        "days_active": len(by_day),
        "projects": sorted(projects),
        "prompts_by_day": {day: len(items) for day, items in sorted(by_day.items())},
    }


def format_as_markdown(data: dict) -> str:
    """Format extracted data as markdown for easy reading."""
    lines = [
        f"# Session Extract — Last {data['days_back']} days",
        "",
        f"**Extracted:** {data['extracted_at'][:10]}",
        f"**Total prompts:** {data['summary']['total_prompts']}",
        f"**Days active:** {data['summary']['days_active']}",
        f"**Projects:** {', '.join(data['summary']['projects']) or 'None'}",
        "",
        "## Activity by Day",
        "",
    ]

    for day, count in sorted(data["summary"]["prompts_by_day"].items()):
        lines.append(f"- {day}: {count} prompts")

    lines.extend(["", "## All Prompts", ""])

    current_day = None
    for prompt in data["prompts"]:
        dt = parse_timestamp(prompt["timestamp"])
        day = dt.strftime("%Y-%m-%d") if dt else "Unknown"

        if day != current_day:
            lines.extend(["", f"### {day}", ""])
            current_day = day

        content = prompt["content"]
        if len(content) > 500:
            content = content[:500] + "..."

        lines.append(f"**{prompt['date']}** ({prompt['project']})")
        lines.append(f"> {content}")
        lines.append("")

    return "\n".join(lines)


def resolve_output_path(args) -> Path | None:
    """Determine the output file path from arguments."""
    if args.output:
        return Path(args.output)

    if args.output_dir:
        now = datetime.now()
        year = now.strftime("%Y")
        week = now.strftime("%W")
        output_dir = Path(args.output_dir) / year
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"retro-notes-{year}-W{week}.md"

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Extract Claude Code sessions for personal retrospectives"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to look back (default: 7)"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory — file is auto-named as retro-notes-YYYY-WNN.md",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    args = parser.parse_args()

    projects_dir = Path.home() / ".claude" / "projects"
    sessions = find_sessions(projects_dir, args.days)
    prompts = extract_user_prompts(sessions)
    summary = generate_summary(prompts)

    output = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "days_back": args.days,
        "summary": summary,
        "prompts": prompts,
    }

    if args.format == "markdown":
        result = format_as_markdown(output)
    else:
        result = json.dumps(output, indent=2)

    output_path = resolve_output_path(args)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Output written to {output_path}")
    else:
        print(result)


if __name__ == "__main__":
    main()
