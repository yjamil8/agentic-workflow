#!/usr/bin/env python3
"""Render an implementation-plan markdown file into the standalone
styled HTML presentation format (Bricolage Grotesque / Source Serif / JetBrains
Mono, green-ink-on-paper theme, table of contents, meta chips).

This is a small, purpose-built markdown subset converter (headers, paragraphs,
bold/italic/code spans, fenced code blocks, GFM pipe tables, ordered/unordered
lists, blockquotes, links) rather than a general CommonMark implementation. It
covers the common constructs used in a typical implementation_plans/ tree.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
KEY_VALUE_RE = re.compile(r"^([A-Z][A-Za-z0-9 /'\-]{1,40}):\s+(.*)$")
MILESTONE_TITLE_RE = re.compile(r"^(M\d+|Milestone\s+[\w.-]+)\b[:.]?\s*(.*)$", re.I)
DONE_SUFFIX_RE = re.compile(r"\s*[\u2013\u2014:\-]?\s*\(?(done|complete|completed)\)?\s*$", re.I)
OWNER_DECISION_TITLE_RE = re.compile(r"owner (decision|choice)", re.I)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text or "section"


def render_inline(text: str) -> str:
    text = html.escape(text, quote=False)

    def code_sub(m: re.Match) -> str:
        return f"<code>{m.group(1)}</code>"

    # Protect inline code from further inline substitution.
    placeholders: list[str] = []

    def stash_code(m: re.Match) -> str:
        placeholders.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(placeholders) - 1}\x00"

    text = INLINE_CODE_RE.sub(stash_code, text)
    text = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", text)

    def unstash(m: re.Match) -> str:
        return placeholders[int(m.group(1))]

    text = re.sub(r"\x00(\d+)\x00", unstash, text)
    return text


@dataclass
class Section:
    level: int
    title: str
    anchor: str
    html_parts: list[str] = field(default_factory=list)


NUMERIC_CELL_RE = re.compile(r"^-?[\d,]+(\.\d+)?%?$")


def split_table_row(line: str) -> list[str]:
    """Split a GFM pipe-table row into cells, treating backtick code spans as
    atomic so a literal `|` inside `code` does not create a spurious column."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    i = 0
    while i < len(stripped):
        ch = stripped[i]
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
        elif ch == "|" and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def parse_table(lines: list[str], start: int) -> tuple[str, int]:
    header_cells = split_table_row(lines[start])
    align_cells = split_table_row(lines[start + 1])
    aligns = []
    for cell in align_cells:
        if cell.endswith(":") and cell.startswith(":"):
            aligns.append("center")
        elif cell.endswith(":"):
            aligns.append("right")
        else:
            aligns.append(None)

    rows = []
    i = start + 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(split_table_row(lines[i]))
        i += 1

    # Fill in alignment for columns with no explicit marker: right-align a
    # column where every body cell looks numeric.
    for idx in range(len(header_cells)):
        if idx < len(aligns) and aligns[idx] is not None:
            continue
        col_cells = [row[idx] for row in rows if idx < len(row) and row[idx]]
        if col_cells and all(NUMERIC_CELL_RE.match(c) for c in col_cells):
            if idx < len(aligns):
                aligns[idx] = "right"
            else:
                aligns.append("right")
        elif idx >= len(aligns):
            aligns.append("left")
        elif aligns[idx] is None:
            aligns[idx] = "left"

    out = ['<div class="table-wrap"><table><thead><tr>']
    for idx, cell in enumerate(header_cells):
        align = aligns[idx] if idx < len(aligns) else "left"
        cls = ' class="num"' if align == "right" else ""
        out.append(f"<th{cls}>{render_inline(cell)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        for idx, cell in enumerate(row):
            align = aligns[idx] if idx < len(aligns) else "left"
            cls = ' class="num"' if align == "right" else ""
            out.append(f"<td{cls}>{render_inline(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out), i


def parse_list(lines: list[str], start: int) -> tuple[str, int]:
    first = lines[start]
    ordered = bool(re.match(r"^\s*\d+\.\s", first))
    tag = "ol" if ordered else "ul"
    item_re = re.compile(r"^\s*(?:\d+\.|[-*])\s+(.*)$")
    items: list[str] = []
    i = start
    while i < len(lines):
        m = item_re.match(lines[i])
        if not m:
            break
        text = m.group(1)
        i += 1
        # Fold in wrapped continuation lines (indented, non-list, non-blank).
        while i < len(lines) and lines[i].strip() and not item_re.match(lines[i]) and lines[i].startswith(" "):
            text += " " + lines[i].strip()
            i += 1
        items.append(render_inline(text))
    body = "".join(f"<li>{item}</li>" for item in items)
    return f"<{tag}>{body}</{tag}>", i


def parse_decision_list(lines: list[str], start: int) -> tuple[str, int]:
    """Render a list inside an 'Owner decisions required' section as the
    lettered decision-card grid, splitting each item's trailing
    'Recommendation: ...' clause into its own muted line."""
    item_re = re.compile(r"^\s*(?:\d+\.|[-*])\s+(.*)$")
    items: list[str] = []
    i = start
    while i < len(lines):
        m = item_re.match(lines[i])
        if not m:
            break
        text = m.group(1)
        i += 1
        while i < len(lines) and lines[i].strip() and not item_re.match(lines[i]) and lines[i].startswith(" "):
            text += " " + lines[i].strip()
            i += 1
        items.append(text)

    out = ['<div class="decisions">']
    for idx, text in enumerate(items):
        letter = chr(ord("a") + idx) if idx < 26 else str(idx + 1)
        rec_match = re.search(r"\bRecommendation:\s*(.*)$", text, re.I)
        if rec_match:
            main_text = text[: rec_match.start()].strip()
            rec_text = rec_match.group(1).strip()
            body_html = f"<p>{render_inline(main_text)}</p><p class=\"rec\">Recommendation: {render_inline(rec_text)}</p>"
        else:
            body_html = f"<p>{render_inline(text)}</p>"
        out.append(f'<div class="decision"><span class="k">{letter}</span><div>{body_html}</div></div>')
    out.append("</div>")
    return "".join(out), i


def render_markdown_body(text: str) -> tuple[list[Section], list[str]]:
    lines = text.split("\n")
    sections: list[Section] = []
    front_matter: list[str] = []
    current: Section | None = None
    seen_anchors: set[str] = set()

    def emit(html_fragment: str) -> None:
        if current is not None:
            current.html_parts.append(html_fragment)
        else:
            front_matter.append(html_fragment)

    i = 0
    n = len(lines)
    para_buf: list[str] = []

    def flush_para() -> None:
        if para_buf:
            joined = " ".join(l.strip() for l in para_buf)
            emit(f"<p>{render_inline(joined)}</p>")
            para_buf.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            flush_para()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                i += 1
                continue  # title handled separately by caller
            anchor = slugify(title)
            base = anchor
            suffix = 2
            while anchor in seen_anchors:
                anchor = f"{base}-{suffix}"
                suffix += 1
            seen_anchors.add(anchor)
            current = Section(level=level, title=title, anchor=anchor)
            sections.append(current)
            i += 1
            continue

        if re.match(r"^(?:-{3,}|\*{3,}|_{3,})$", stripped):
            flush_para()
            emit("<hr>")
            i += 1
            continue

        if stripped.startswith("```"):
            flush_para()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code_html = html.escape("\n".join(code_lines))
            emit(f"<pre><code>{code_html}</code></pre>")
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:\-|]+\|?$", lines[i + 1].strip()):
            flush_para()
            table_html, next_i = parse_table(lines, i)
            emit(table_html)
            i = next_i
            continue

        if current is None and re.match(r"^\s*[-*]\s+", line):
            item_re = re.compile(r"^\s*[-*]\s+(.*)$")
            j = i
            items = []
            while j < n and item_re.match(lines[j]):
                items.append(item_re.match(lines[j]).group(1).strip())
                j += 1
            if items and all(KEY_VALUE_RE.match(it) for it in items):
                flush_para()
                for it in items:
                    emit(f"<p>{render_inline(it)}</p>")
                i = j
                continue

        if re.match(r"^\s*(?:\d+\.|[-*])\s+", line):
            flush_para()
            in_decisions_section = current is not None and OWNER_DECISION_TITLE_RE.search(current.title)
            if in_decisions_section:
                list_html, next_i = parse_decision_list(lines, i)
            else:
                list_html, next_i = parse_list(lines, i)
            emit(list_html)
            i = next_i
            continue

        if stripped.startswith(">"):
            flush_para()
            quote_lines = []
            while i < n and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip().lstrip(">").strip())
                i += 1
            quote_text = " ".join(quote_lines)
            emit(f'<div class="note">{render_inline(quote_text)}</div>')
            continue

        if current is None and KEY_VALUE_RE.match(stripped):
            flush_para()
            emit(f"<p>{render_inline(stripped)}</p>")
            i += 1
            continue

        para_buf.append(line)
        i += 1

    flush_para()
    return sections, front_matter


def render_plan_html(md_text: str, source_label: str, sidebar_html: str | None = None) -> str:
    lines = md_text.split("\n")
    title = "Implementation Plan"
    for line in lines:
        m = re.match(r"^#\s+(.*)$", line.strip())
        if m:
            title = m.group(1).strip()
            break

    sections, front_matter = render_markdown_body(md_text)

    meta_chips: list[tuple[str, str]] = []
    lede_parts: list[str] = []
    for frag in front_matter:
        m = re.match(r"^<p>(.*)</p>$", frag, re.S)
        text = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))) if m else ""
        kv = KEY_VALUE_RE.match(text)
        if kv and len(kv.group(2)) <= 100:
            meta_chips.append((kv.group(1), kv.group(2)))
        elif kv:
            # Too long for a one-line chip; keep it as a labeled note instead.
            lede_parts.append(f"<p><strong>{html.escape(kv.group(1))}:</strong> {render_inline(kv.group(2))}</p>")
        elif text or m is None:
            # Lists, tables, code blocks, and notes above the first section stay visible.
            lede_parts.append(frag)

    meta_chips.append(("Source", source_label))

    toc_items = "".join(
        f'<li><a href="#{s.anchor}">{html.escape(s.title)}</a></li>'
        for s in sections
        if s.level == 2
    )

    body_sections = []
    for s in sections:
        tag = "h2" if s.level == 2 else "h3"
        milestone_match = MILESTONE_TITLE_RE.match(s.title) if s.level in (2, 3) else None
        if milestone_match:
            title_text = s.title
            done_match = DONE_SUFFIX_RE.search(title_text)
            badge_html = ""
            if done_match:
                title_text = title_text[: done_match.start()].rstrip()
                badge_html = f' <span class="done">{html.escape(done_match.group(1).lower())}</span>'
            heading_html = f'<{tag} id="{s.anchor}">{html.escape(title_text)}{badge_html}</{tag}>'
            body_sections.append(f'<div class="milestone">{heading_html}{"".join(s.html_parts)}</div>')
        else:
            body_sections.append(f'<{tag} id="{s.anchor}">{html.escape(s.title)}</{tag}>')
            body_sections.extend(s.html_parts)

    meta_html = "".join(
        f"<span><b>{html.escape(k)}</b> {html.escape(v)}</span>" for k, v in meta_chips
    )
    lede_html = "".join(lede_parts)

    page_html = f"""<div class="page">
  <h1>{html.escape(title)}</h1>
  <div class="meta">{meta_html}</div>
  <div class="lede">{lede_html}</div>
  <nav class="toc" aria-label="Sections"><ol>{toc_items}</ol></nav>
  {''.join(body_sections)}
</div>"""

    if sidebar_html is not None:
        body_html = f"""<button class="nav-toggle" id="planNavToggle" type="button" aria-label="Toggle plan navigation" title="Browse plans">&#9776;</button>
<button class="theme-toggle" id="planThemeToggle" type="button" aria-label="Toggle dark and light mode" title="Toggle theme">&#9681;</button>
<div class="shell">
  <div class="nav-backdrop" id="planNavBackdrop"></div>
  <nav class="sidebar" id="planSidebar" aria-label="Other plans">{sidebar_html}</nav>
  <div class="content">{page_html}</div>
</div>
<script>
(function () {{
  var navToggle = document.getElementById("planNavToggle");
  var backdrop = document.getElementById("planNavBackdrop");
  function setNavOpen(open) {{
    document.body.classList.toggle("nav-open", open);
  }}
  navToggle.addEventListener("click", function () {{
    setNavOpen(!document.body.classList.contains("nav-open"));
  }});
  backdrop.addEventListener("click", function () {{ setNavOpen(false); }});
}})();
</script>"""
    else:
        body_html = f"""<button class="theme-toggle" id="planThemeToggle" type="button" aria-label="Toggle dark and light mode" title="Toggle theme">&#9681;</button>
{page_html}"""

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
{PLAN_CSS}
</style>
</head><body>
{body_html}
<script>
(function () {{
  var root = document.documentElement;
  var key = "agentic-workflow-plan-theme";
  var btn = document.getElementById("planThemeToggle");
  var stored = null;
  try {{ stored = localStorage.getItem(key); }} catch (e) {{}}
  if (stored === "light" || stored === "dark") root.setAttribute("data-theme", stored);
  btn.addEventListener("click", function () {{
    var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var current = root.getAttribute("data-theme") || (systemDark ? "dark" : "light");
    var next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {{ localStorage.setItem(key, next); }} catch (e) {{}}
  }});
}})();
</script>
</body></html>"""


PLAN_CSS = """
:root {
  color-scheme: light dark;
  --ground: #f6f8f7; --paper: #ffffff; --ink: #142019; --muted: #5a6a62;
  --line: #d6e0da; --tint: #e6f4ec; --accent: #0f8f5a; --accent-ink: #0a6a43;
  --code-bg: #eef2f0;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #0b100e; --paper: #10171359; --ink: #e7efea; --muted: #9cada4;
    --line: #22302a; --tint: #112419; --accent: #33d98c; --accent-ink: #7fe9b7;
    --code-bg: #141d18;
  }
}
:root[data-theme="dark"] {
  --ground: #0b100e; --paper: #10171359; --ink: #e7efea; --muted: #9cada4;
  --line: #22302a; --tint: #112419; --accent: #33d98c; --accent-ink: #7fe9b7;
  --code-bg: #141d18;
}
body { margin: 0; background: var(--ground); color: var(--ink);
  font-family: "Source Serif 4", Georgia, "Times New Roman", serif; font-size: 17px; line-height: 1.6; }
.page { max-width: 76ch; margin: 0 auto; padding-block: 40px 96px; padding-inline: 20px; overflow-wrap: break-word; }
h1, h2, h3 { font-family: "Bricolage Grotesque", "Helvetica Neue", Arial, sans-serif; text-wrap: balance; line-height: 1.12; margin: 0; }
h1 { font-size: clamp(2rem, 5vw, 2.9rem); font-weight: 700; letter-spacing: -0.02em; }
h2 { font-size: 1.45rem; font-weight: 700; margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--line); }
h3 { font-size: 1.08rem; font-weight: 700; margin-top: 1.8rem; }
p { margin: 0.75rem 0; max-width: 68ch; }
ul, ol { padding-left: 1.3rem; margin: 0.6rem 0; }
li { margin: 0.35rem 0; max-width: 66ch; }
li::marker { color: var(--accent); }
a { color: var(--accent-ink); }
.meta { display: flex; flex-wrap: wrap; gap: 0.5rem 1.4rem; margin-top: 1rem;
  font-family: "JetBrains Mono", ui-monospace, Menlo, monospace; font-size: 0.78rem; color: var(--muted); }
.meta span { max-width: 100%; overflow-wrap: anywhere; }
.meta b { color: var(--ink); font-weight: 500; }
.lede { font-size: 1.12rem; margin-top: 1.4rem; color: var(--ink); }
.toc { margin: 1.6rem 0 0; padding: 1rem 1.2rem; background: var(--tint); border-radius: 10px; }
.toc ol { columns: 2; column-gap: 2rem; margin: 0.3rem 0 0; padding-left: 1.2rem; }
.toc li { break-inside: avoid; margin: 0.2rem 0; font-family: "Bricolage Grotesque", sans-serif; font-size: 0.92rem; }
.toc a { text-decoration: none; }
.toc a:hover, .toc a:focus-visible { text-decoration: underline; }
code, kbd { font-family: "JetBrains Mono", ui-monospace, Menlo, monospace; font-size: 0.83em;
  background: var(--code-bg); padding: 0.1em 0.35em; border-radius: 4px; overflow-wrap: anywhere; }
pre { overflow-x: auto; padding: 0.9rem 1rem; background: var(--code-bg); border-radius: 8px; font-size: 0.8rem; line-height: 1.5; }
pre code { background: none; padding: 0; font-size: inherit; }
.table-wrap { overflow-x: auto; margin: 0.8rem 0; }
table { border-collapse: collapse; width: 100%; font-size: 0.92rem; }
th, td { text-align: left; padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-family: "Bricolage Grotesque", sans-serif; font-weight: 700; font-size: 0.8rem; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--muted); }
td.num, th.num { font-family: "JetBrains Mono", monospace; font-variant-numeric: tabular-nums; text-align: right; }
hr { border: none; border-top: 1px solid var(--line); margin: 2rem 0; }
.note { padding: 0.8rem 1rem; background: var(--tint); border-radius: 8px; margin: 1rem 0; max-width: 68ch; }
.decisions { display: grid; gap: 0.7rem; margin: 0.8rem 0; }
.decision { display: grid; grid-template-columns: 2.2rem minmax(0, 1fr); gap: 0.6rem; align-items: start; }
.decision .k { font-family: "Bricolage Grotesque", sans-serif; font-weight: 700; font-size: 0.85rem;
  color: var(--accent-ink); padding-top: 0.15rem; }
.decision p { margin: 0; }
.decision .rec { color: var(--muted); font-size: 0.95rem; margin-top: 0.35rem; }
.milestone { border-left: 3px solid var(--accent); padding: 0.2rem 0 0.2rem 1rem; margin: 1.2rem 0; }
.milestone h3 { margin-top: 0; }
.milestone .done { color: var(--accent-ink); font-family: "Bricolage Grotesque", sans-serif;
  font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }
.theme-toggle, .nav-toggle { position: fixed; top: 16px; z-index: 21;
  display: inline-flex; align-items: center; justify-content: center;
  width: 2.25rem; height: 2.25rem; border-radius: 999px; border: 1px solid var(--line);
  background: var(--paper); color: var(--ink); cursor: pointer; font-size: 1.05rem; line-height: 1; }
.theme-toggle { right: 16px; }
.nav-toggle { left: 16px; display: none; }
.theme-toggle:hover, .theme-toggle:focus-visible,
.nav-toggle:hover, .nav-toggle:focus-visible { border-color: var(--accent); }
.shell { display: flex; align-items: flex-start; min-height: 100vh; }
.sidebar { flex: 0 0 260px; width: 260px; box-sizing: border-box; border-right: 1px solid var(--line);
  padding: 64px 0 40px; position: sticky; top: 0; height: 100vh; overflow-y: auto; background: var(--ground); }
.sidebar-section { padding: 0 0.5rem 1.2rem; margin: 0 0.5rem 1rem; border-bottom: 1px solid var(--line); }
.sidebar-section:last-child { border-bottom: none; }
.sidebar-title { font-family: "Bricolage Grotesque", sans-serif; font-size: 0.7rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin: 0 0 0.4rem; padding: 0 0.4rem; }
.sidebar-home { display: block; padding: 0.35rem 0.4rem; font-family: "Bricolage Grotesque", sans-serif;
  font-size: 0.88rem; font-weight: 700; text-decoration: none; color: var(--ink); border-radius: 6px; }
.sidebar-home:hover, .sidebar-home:focus-visible { background: var(--tint); }
.plan-link { display: block; padding: 0.4rem 0.5rem; margin: 0 0 0.1rem; border-radius: 6px; text-decoration: none; }
.plan-link:hover, .plan-link:focus-visible { background: var(--tint); }
.plan-link.active { background: var(--tint); box-shadow: inset 3px 0 0 var(--accent); }
.plan-link-date { display: block; font-family: "JetBrains Mono", monospace; font-size: 0.66rem; color: var(--muted); }
.plan-link-name { display: block; font-size: 0.82rem; line-height: 1.3; overflow-wrap: anywhere; color: var(--ink); }
.sidebar-more { display: block; padding: 0.5rem 0.5rem 0; font-size: 0.82rem; color: var(--accent-ink); text-decoration: none; }
.sidebar-more:hover, .sidebar-more:focus-visible { text-decoration: underline; }
.content { flex: 1; min-width: 0; }
.nav-backdrop { display: none; }
@media (max-width: 900px) {
  .nav-toggle { display: inline-flex; }
  .sidebar { position: fixed; top: 0; left: 0; z-index: 20; width: min(85vw, 320px); flex: none;
    padding-top: 64px; transform: translateX(-100%); transition: transform 0.2s ease;
    box-shadow: 2px 0 16px rgba(0, 0, 0, 0.25); }
  body.nav-open .sidebar { transform: translateX(0); }
  .nav-backdrop { display: block; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.45); z-index: 19;
    opacity: 0; pointer-events: none; transition: opacity 0.2s ease; }
  body.nav-open .nav-backdrop { opacity: 1; pointer-events: auto; }
}
@media (max-width: 560px) { .toc ol { columns: 1; } body { font-size: 16px; }
  .theme-toggle, .nav-toggle { top: 10px; }
  .theme-toggle { right: 10px; } .nav-toggle { left: 10px; } }
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto; } .sidebar { transition: none; } .nav-backdrop { transition: none; } }
"""


def main() -> int:
    import sys
    from pathlib import Path

    if len(sys.argv) != 2:
        print("usage: plan_renderer.py <path-to-plan.md>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    print(render_plan_html(text, str(path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
