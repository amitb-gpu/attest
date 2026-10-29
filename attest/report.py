"""Report generator: ledger -> markdown, no model calls."""
from __future__ import annotations


def render_markdown(ledger) -> str:
    lines = [
        f"# Attest report — {ledger.run_id}",
        "",
        f"**Headline: {ledger.headline}**",
        "",
        "## Checks",
        "",
        "| Check | Verdict | Evidence |",
        "|---|---|---|",
    ]
    for c in ledger.checks:
        lines.append(f"| {c.name} | {c.verdict} | {c.evidence} |")
    lines += ["", "## Notes", ""]
    for n in ledger.notes:
        lines.append(f"- {n}")
    lines.append("")
    return "\n".join(lines)
