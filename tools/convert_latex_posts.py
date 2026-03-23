#!/usr/bin/env python3
"""Convert LaTeX blog posts into Quarto .qmd files."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LATEX_DIR = REPO_ROOT / "blog" / "latex"
BLOG_DIR = REPO_ROOT / "blog"
GENERATED_NOTICE = (
    "<!-- AUTO-GENERATED from blog/latex source. "
    "Edit the .tex file instead. -->"
)


def extract_commented_yaml(tex_text: str) -> tuple[str, str]:
    """Extract initial %-commented YAML front matter from a .tex file."""
    lines = tex_text.splitlines(keepends=True)
    first_content_line = 0
    while first_content_line < len(lines) and lines[first_content_line].strip() == "":
        first_content_line += 1

    if first_content_line >= len(lines):
        return "", tex_text

    opening = re.match(r"^\s*%\s*---\s*$", lines[first_content_line].strip("\n"))
    if not opening:
        return "", tex_text

    closing_index = None
    for idx in range(first_content_line + 1, len(lines)):
        if re.match(r"^\s*%\s*---\s*$", lines[idx].strip("\n")):
            closing_index = idx
            break

    if closing_index is None:
        return "", tex_text

    yaml_lines = []
    for line in lines[first_content_line + 1 : closing_index]:
        # Strip one leading '%' marker from commented YAML lines.
        yaml_lines.append(re.sub(r"^\s*%\s?", "", line.rstrip("\n")))

    remaining = "".join(lines[:first_content_line] + lines[closing_index + 1 :])
    yaml_text = "\n".join(yaml_lines).strip()
    return yaml_text, remaining


def convert_sidework_blocks(markdown_text: str) -> str:
    """Convert LaTeX sidework environment markers to Quarto margin divs."""
    output_lines: list[str] = []
    in_sidework = False

    for line in markdown_text.splitlines():
        # Pandoc often maps unknown LaTeX environments to fenced divs.
        if re.match(r"^\s*:::\s*sidework\s*$", line) or re.match(
            r"^\s*:::\s*\{[^}]*\.sidework[^}]*\}\s*$", line
        ):
            output_lines.append("::: column-margin")
            in_sidework = True
            continue
        if re.match(r"^\s*\\begin\{sidework\}\s*$", line):
            output_lines.append("::: column-margin")
            in_sidework = True
            continue
        if in_sidework and re.match(r"^\s*:::\s*$", line):
            output_lines.append(":::")
            in_sidework = False
            continue
        if re.match(r"^\s*\\end\{sidework\}\s*$", line):
            output_lines.append(":::")
            in_sidework = False
            continue
        output_lines.append(line)

    if in_sidework:
        output_lines.append(":::")

    return "\n".join(output_lines).rstrip() + "\n"


def run_pandoc(latex_text: str, pandoc_cmd: list[str]) -> str:
    """Convert latex body text to Quarto-friendly markdown."""
    result = subprocess.run(
        [
            *pandoc_cmd,
            "--from=latex",
            "--to=markdown+tex_math_dollars+fenced_divs",
        ],
        input=latex_text,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Pandoc conversion failed.")
    return result.stdout


def resolve_inputs(only: str | None) -> list[Path]:
    if only:
        candidate = Path(only)
        if not candidate.is_absolute():
            candidate = (REPO_ROOT / only).resolve()
        if not candidate.exists():
            fallback = LATEX_DIR / only
            if fallback.exists():
                candidate = fallback
            else:
                raise FileNotFoundError(
                    f"Requested source file does not exist: {only}"
                )
        if candidate.suffix != ".tex":
            raise ValueError("The --only input must be a .tex file.")
        return [candidate]

    tex_files = sorted(LATEX_DIR.glob("*.tex"))
    return [
        path
        for path in tex_files
        if not path.name.startswith("_") and path.name != "post_template.tex"
    ]


def resolve_pandoc_command(pandoc_bin: str) -> list[str]:
    if Path(pandoc_bin).exists() or shutil.which(pandoc_bin):
        return [pandoc_bin]

    # Common local setup: pandoc is bundled through Quarto.
    if pandoc_bin == "pandoc" and shutil.which("quarto"):
        return ["quarto", "pandoc"]

    raise FileNotFoundError(
        f"Could not find pandoc executable: '{pandoc_bin}'. "
        "Install Pandoc/Quarto or pass --pandoc-path."
    )


def render_one(tex_path: Path, pandoc_cmd: list[str], dry_run: bool) -> Path:
    raw_text = tex_path.read_text(encoding="utf-8")
    yaml_text, latex_body = extract_commented_yaml(raw_text)
    markdown = run_pandoc(latex_body, pandoc_cmd)
    markdown = convert_sidework_blocks(markdown)

    sections = []
    if yaml_text:
        sections.extend(["---", yaml_text, "---", ""])
    sections.extend([GENERATED_NOTICE, "", markdown.rstrip(), ""])
    output_text = "\n".join(sections)

    output_path = BLOG_DIR / f"{tex_path.stem}.qmd"
    if dry_run:
        print(f"[dry-run] Would write {output_path.relative_to(REPO_ROOT)}")
    else:
        output_path.write_text(output_text, encoding="utf-8")
        print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert LaTeX blog posts (blog/latex/*.tex) to blog/*.qmd"
    )
    parser.add_argument(
        "--only",
        help="Convert a single .tex file (absolute path or repo-relative path).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned outputs without writing files.",
    )
    parser.add_argument(
        "--pandoc-path",
        default=os.environ.get("PANDOC_PATH", "pandoc"),
        help="Pandoc binary path or command name (default: pandoc).",
    )
    args = parser.parse_args()

    try:
        pandoc_cmd = resolve_pandoc_command(args.pandoc_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not LATEX_DIR.exists():
        print(
            "No blog/latex directory found. "
            "Create it and add .tex posts before running conversion."
        )
        return 0

    try:
        tex_inputs = resolve_inputs(args.only)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not tex_inputs:
        print("No .tex files found in blog/latex; nothing to convert.")
        return 0

    failed = False
    for tex_path in tex_inputs:
        try:
            render_one(tex_path, pandoc_cmd, args.dry_run)
        except Exception as exc:  # noqa: BLE001
            failed = True
            print(
                f"ERROR converting {tex_path.relative_to(REPO_ROOT)}: {exc}",
                file=sys.stderr,
            )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
