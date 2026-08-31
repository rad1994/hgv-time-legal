"""
Generator statycznej strony z dokumentami prawnymi HGV Time Directive.

Zrodlem prawdy sa pliki markdown w vaulcie — ten skrypt tylko je sklada
w strone. Dzieki temu poprawka tekstu idzie w jednym miejscu, a nie w dwoch
rozjezdzajacych sie kopiach: wersji dla Google i wersji dla siebie.
"""

import html
import re
from pathlib import Path

VAULT = Path(r"C:\Users\mms19\Documents\Obsidian Vault\HGV app\00-Product")
OUT = Path(__file__).parent

# Uzupelniane przed publikacja. Pusty string = placeholder zostaje widoczny.
VALUES = {
    "[CONTACT EMAIL]": "",
    "[EFFECTIVE DATE]": "",
    "[LEGAL ENTITY]": "",
}

PAGES = [
    ("08-Privacy-Policy.md", "index.html", "Privacy Policy", "Privacy Policy"),
    ("09-Terms-of-Service.md", "terms.html", "Terms of Service", "Terms of Service"),
]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — HGV Time</title>
<style>
  :root {{
    --bg: #ffffff; --surface: #f5f6f8; --text: #14181f; --muted: #5a6675;
    --border: #dfe3e8; --accent: #1f7a45;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #10141a; --surface: #171d25; --text: #e9edf2; --muted: #9aa6b4;
      --border: #262f3a; --accent: #22c55e;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  .wrap {{ max-width: 46rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}
  nav {{
    display: flex; gap: 1.25rem; padding-bottom: 1.25rem; margin-bottom: 2rem;
    border-bottom: 1px solid var(--border); font-size: .95rem;
  }}
  nav a {{ color: var(--muted); text-decoration: none; }}
  nav a:hover {{ color: var(--text); }}
  nav a[aria-current] {{ color: var(--accent); font-weight: 600; }}
  h1 {{ font-size: 1.85rem; line-height: 1.2; margin: 0 0 .5rem; }}
  h2 {{ font-size: 1.15rem; margin: 2.25rem 0 .5rem; }}
  h3 {{ font-size: 1rem; margin: 1.75rem 0 .5rem; }}
  p, li {{ color: var(--text); }}
  ul {{ padding-left: 1.25rem; }}
  li {{ margin: .35rem 0; }}
  strong {{ font-weight: 650; }}
  .updated {{ color: var(--muted); font-size: .95rem; margin: 0 0 2rem; }}
  .todo {{
    background: var(--surface); border: 1px solid var(--border);
    border-left: 3px solid var(--accent); border-radius: .4rem;
    padding: .85rem 1rem; margin: 1.5rem 0; color: var(--muted); font-size: .95rem;
  }}
  footer {{
    margin-top: 3rem; padding-top: 1.25rem; border-top: 1px solid var(--border);
    color: var(--muted); font-size: .9rem;
  }}
  a {{ color: var(--accent); }}
</style>
</head>
<body>
<div class="wrap">
<nav>
  <a href="./"{privacy_current}>Privacy Policy</a>
  <a href="./terms.html"{terms_current}>Terms of Service</a>
</nav>
{body}
<footer>HGV Time — a driving hours and working time assistant for professional drivers.</footer>
</div>
</body>
</html>
"""


def strip_front_matter_and_notes(text: str) -> str:
    """Usuwa frontmatter i polskie notatki robocze — na strone ida same dokumenty."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    # Wszystko przed pozioma linia to notatki dla wlasciciela, nie tresc prawna.
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]
    return text.strip()


def render(markdown: str) -> str:
    """Pierwszy naglowek dokumentu staje sie h1 strony — jedna strona, jeden tytul."""
    out, in_list, seen_heading = [], False, False
    for raw in markdown.split("\n"):
        line = raw.rstrip()
        if not line:
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        if line.startswith("## ") and not seen_heading:
            seen_heading = True
            out.append(f"<h1>{inline(line[3:])}</h1>")
            continue
        if line.startswith("### "):
            level, content = "h3", line[4:]
        elif line.startswith("## "):
            level, content = "h2", line[3:]
        elif line.startswith("# "):
            level, content = "h1", line[2:]
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        else:
            level, content = "p", line
        if in_list:
            out.append("</ul>")
            in_list = False
        css = ' class="updated"' if content.startswith("**Last updated") else ""
        out.append(f"<{level}{css}>{inline(content)}</{level}>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    for placeholder, value in VALUES.items():
        marker = html.escape(placeholder)
        if value:
            text = text.replace(marker, html.escape(value))
        else:
            text = text.replace(marker, f'<span class="todo">{marker} — do uzupełnienia</span>')
    return text


for source, target, title, nav_title in PAGES:
    body = render(strip_front_matter_and_notes((VAULT / source).read_text(encoding="utf-8")))
    page = TEMPLATE.format(
        title=title,
        body=body,
        privacy_current=' aria-current="page"' if target == "index.html" else "",
        terms_current=' aria-current="page"' if target == "terms.html" else "",
    )
    (OUT / target).write_text(page, encoding="utf-8")
    print(f"{target}: {len(page)} bytes")
