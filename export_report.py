# ruff: noqa: E501
"""Export the executed notebook as a professional self-contained HTML report."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import nbformat
from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
from traitlets.config import Config

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "notebooks" / "FAANGM_Narrative_to_Numbers.ipynb"
OUTPUT = ROOT / "notebooks" / "FAANGM_Narrative_to_Numbers.html"

THEME = """
:root {
  --ink: #19242b;
  --muted: #5d6970;
  --paper: #f7f6f2;
  --surface: #ffffff;
  --teal: #1f6f6d;
  --teal-dark: #124d4b;
  --gold: #c58b22;
  --red: #9b3a36;
  --line: #d9dedb;
  --code: #edf1ef;
}
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  padding: 0 !important;
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  background: var(--paper);
  color: var(--ink);
  font-family: "Avenir Next", Avenir, "Gill Sans", sans-serif;
  font-size: 16px;
  line-height: 1.65;
  letter-spacing: 0;
}
.report-cover {
  min-height: 72vh;
  display: grid;
  align-content: center;
  color: white;
  background:
    linear-gradient(135deg, rgba(18, 77, 75, .95), rgba(25, 36, 43, .97)),
    repeating-linear-gradient(90deg, transparent 0 78px, rgba(255,255,255,.08) 79px 80px);
  border-bottom: 8px solid var(--gold);
}
.cover-inner { width: min(1050px, calc(100% - 48px)); margin: 0 auto; padding: 72px 0; }
.cover-kicker { font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .16em; color: #f2c96f; }
.report-cover h1 {
  max-width: 900px;
  margin: 18px 0 16px;
  color: white;
  font-family: Iowan Old Style, Palatino Linotype, Georgia, serif;
  font-size: clamp(2.6rem, 7vw, 5.8rem);
  line-height: .98;
  letter-spacing: 0;
}
.cover-subtitle { max-width: 780px; font-size: 1.25rem; color: #dce9e7; }
.cover-meta { display: flex; flex-wrap: wrap; gap: 22px; margin-top: 44px; }
.cover-meta span { border-left: 3px solid var(--gold); padding-left: 12px; font-weight: 600; }
.jp-Notebook { width: 100%; max-width: 100%; margin: 0; padding: 0 !important; }
.jp-Cell { width: min(1120px, calc(100% - 40px)); margin: 0 auto 22px; padding: 0; }
.jp-Cell:first-of-type { margin-top: 42px; }
.jp-MarkdownCell { background: transparent !important; }
.jp-MarkdownOutput { font-family: "Avenir Next", Avenir, "Gill Sans", sans-serif; }
.jp-MarkdownOutput h1:first-child { display: none; }
h1, h2, h3 {
  color: var(--ink);
  font-family: Iowan Old Style, Palatino Linotype, Georgia, serif;
  letter-spacing: 0;
}
h2 { margin-top: 64px; padding: 14px 0 10px; border-bottom: 2px solid var(--teal); font-size: 2rem; }
h3 { margin-top: 36px; color: var(--teal-dark); }
p, li { max-width: 920px; }
a { color: var(--teal-dark); text-underline-offset: 3px; }
blockquote { margin: 24px 0; padding: 16px 22px; border-left: 4px solid var(--gold); background: #fff9e9; }
.jp-InputArea, .jp-OutputArea-output {
  border: 1px solid var(--line);
  border-radius: 6px;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}
.jp-InputArea { background: var(--code); }
.jp-OutputArea-output { background: var(--surface); padding: 12px 16px; }
.jp-OutputArea-output pre { white-space: pre-wrap; word-break: break-word; }
.jp-InputArea pre { white-space: pre-wrap !important; overflow-wrap: anywhere; }
pre, code, .highlight { font-family: "SFMono-Regular", Consolas, monospace; font-size: .88rem; }
.table-wrapper { width: 100%; overflow-x: auto; margin: 18px 0 28px; border: 1px solid var(--line); background: white; }
table { width: 100%; border-collapse: collapse; font-size: .88rem; }
th { background: var(--teal-dark); color: white; text-align: left; padding: 10px 12px; position: sticky; top: 0; }
td { padding: 9px 12px; border-bottom: 1px solid #e6e9e7; vertical-align: top; }
tbody tr:nth-child(even) { background: #f4f7f5; }
img { display: block; max-width: 100%; height: auto; margin: 18px auto; }
.output_error { border-color: var(--red) !important; }
.report-footer { background: var(--ink); color: #dce3e1; padding: 28px 24px; text-align: center; font-size: .85rem; }
@media (max-width: 700px) {
  body { font-size: 15px; }
  .cover-inner, .jp-Cell { width: min(100% - 24px, 1120px); }
  .report-cover { min-height: 64vh; }
  .report-cover h1 { font-size: 2.7rem; }
  .cover-meta { display: grid; gap: 12px; }
  h2 { font-size: 1.55rem; margin-top: 48px; }
  .jp-InputArea, .jp-OutputArea-output { border-radius: 3px; }
}
@media print {
  body { background: white; font-size: 10pt; }
  .report-cover { min-height: 96vh; break-after: page; print-color-adjust: exact; }
  .jp-Cell { width: 100%; margin-left: 0; margin-right: 0; }
  h2 { break-before: page; }
  .jp-Cell, table, img { break-inside: avoid; }
  .jp-InputArea { max-height: none; }
  a { color: var(--ink); text-decoration: none; }
}
"""


def validate_notebook(notebook: nbformat.NotebookNode) -> None:
    errors = []
    for index, cell in enumerate(notebook.cells, start=1):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(
                    f"Cell {index}: {output.get('ename')}: {output.get('evalue')}"
                )
    if errors:
        raise RuntimeError("Notebook contains execution errors:\n" + "\n".join(errors))
    rendered = "\n".join(
        str(output.get("text", ""))
        for cell in notebook.cells
        for output in cell.get("outputs", [])
    )
    if "DELIVERABLE CHECKS PASSED: 12/12" not in rendered:
        raise RuntimeError("Notebook is missing the final deliverable pass signal")


def add_report_theme(html: str) -> str:
  soup = BeautifulSoup(html, "html.parser")
  soup.title.string = "FAANG+M Narrative-to-Numbers Research Desk"
  style = soup.new_tag("style")
  style.string = THEME
  soup.head.append(style)

  cover = soup.new_tag(
    "header", attrs={"class": "report-cover", "id": "report-cover"}
  )
  inner = soup.new_tag("div", attrs={"class": "cover-inner"})
  kicker = soup.new_tag("div", attrs={"class": "cover-kicker"})
  kicker.string = "AAI-520 | Final Team Project"
  title = soup.new_tag("h1")
  title.string = "FAANG+M Narrative-to-Numbers"
  subtitle = soup.new_tag("p", attrs={"class": "cover-subtitle"})
  subtitle.string = (
    "An auditable multi-agent research desk connecting AI narratives, "
    "financial execution, news sentiment, and market confirmation."
  )
  meta = soup.new_tag("div", attrs={"class": "cover-meta"})
  for text in (
    "6 companies",
    "3 required workflows",
    "12/12 checks",
    "As of Sep 7, 2026",
  ):
    item = soup.new_tag("span")
    item.string = text
    meta.append(item)
  inner.extend([kicker, title, subtitle, meta])
  cover.append(inner)
  soup.body.insert(0, cover)

  for table in soup.find_all("table"):
    if table.parent and "table-wrapper" in table.parent.get("class", []):
      continue
    wrapper = soup.new_tag("div", attrs={"class": "table-wrapper"})
    table.wrap(wrapper)

  footer = soup.new_tag(
    "footer", attrs={"class": "report-footer", "id": "report-footer"}
  )
  footer.string = (
    f"FAANG+M Narrative-to-Numbers Research Desk | Generated {date.today():%B %Y} "
    "| Educational research, not investment advice"
  )
  soup.body.append(footer)
  return str(soup)


def main() -> None:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    validate_notebook(notebook)
    config = Config()
    config.HTMLExporter.exclude_input_prompt = True
    config.HTMLExporter.exclude_output_prompt = True
    exporter = HTMLExporter(config=config, template_name="lab")
    body, _ = exporter.from_notebook_node(notebook)
    OUTPUT.write_text(add_report_theme(body), encoding="utf-8")
    print(f"Exported {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
