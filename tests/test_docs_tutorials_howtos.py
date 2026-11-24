"""Executable documentation, Mermaid, STE, Go toolchain, and CLI checks for freeport."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<ticks>`{3,}|~{3,})(?P<info>.*)$")
BOX_CHAR_RE = re.compile(r"[\u2500-\u257f▼▲◄►]")
FRENCH_MARKERS = re.compile(
    r"\b(?:procédure|tutoriel|démarrage|prérequis|vérification|"
    r"retour\s+arrière|utilisation|générateur)\b",
    re.IGNORECASE,
)
STE_BANNED = re.compile(
    r"(?:;|should\b|would\b|may\b|might\b|shall\b|"
    r"\b(?:don't|doesn't|isn't|aren't|won't|can't|let's)\b)",
    re.IGNORECASE,
)


def _iter_markdown() -> list[Path]:
    """Return all Markdown files in the repository excluding .git."""
    return sorted(p for p in REPO_ROOT.rglob("*.md") if ".git/" not in p.as_posix())


def _extract_fenced_blocks(text: str) -> list[dict[str, object]]:
    """Extract fenced code blocks with indentation and language tag metadata."""
    blocks: list[dict[str, object]] = []
    open_fence: dict[str, object] | None = None
    for idx, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if open_fence is None:
            if match:
                ticks = match.group("ticks")
                open_fence = {
                    "char": ticks[0],
                    "len": len(ticks),
                    "indent": match.group("indent"),
                    "info": match.group("info").strip().lower(),
                    "start_line": idx,
                    "lines": [],
                }
        else:
            if match and match.group("ticks")[0] == open_fence["char"] and len(match.group("ticks")) >= int(open_fence["len"]):
                if not match.group("info").strip():
                    open_fence["code"] = "\n".join(open_fence["lines"])  # type: ignore[arg-type]
                    blocks.append(open_fence)
                    open_fence = None
                    continue
            open_fence["lines"].append(line)  # type: ignore[union-attr]
    if open_fence is not None:
        raise AssertionError(f"Unclosed fenced code block at line {open_fence['start_line']}")
    return blocks


def _strip_code(text: str) -> str:
    """Return Markdown text outside fenced and inline code spans."""
    lines: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if not in_fence:
            if match:
                in_fence = True
                fence_char = match.group("ticks")[0]
                fence_len = len(match.group("ticks"))
            else:
                lines.append(re.sub(r"`[^`]+`", "", line))
        else:
            if match and match.group("ticks")[0] == fence_char and len(match.group("ticks")) >= fence_len and not match.group("info").strip():
                in_fence = False
    return "\n".join(lines)


def _heading_slugs(text: str) -> set[str]:
    """Build GitHub-style heading anchors from Markdown outside code blocks."""
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    for line in _strip_code(text).splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", match.group(1).strip())
        slug = re.sub(r"[^a-z0-9\- ]+", "", raw.lower()).strip().replace(" ", "-")
        slug = re.sub(r"-{2,}", "-", slug)
        if not slug:
            continue
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        slugs.add(slug if seen == 0 else f"{slug}-{seen}")
    return slugs


class TestFreeportDocsAndBuild(unittest.TestCase):
    """Validate Diátaxis docs, STE rules, Mermaid, README fixes, and Go test/vet/fmt checks."""

    def test_diataxis_structure_links_and_ste(self) -> None:
        required = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "go.mod",
            DOCS_DIR / "index.md",
            DOCS_DIR / "01-tutorials" / "index.md",
            DOCS_DIR / "01-tutorials" / "01-cli-and-go-library-quickstart.md",
            DOCS_DIR / "02-how-to-guides" / "index.md",
            DOCS_DIR / "02-how-to-guides" / "allocate-ports-safely-in-go-and-ci.md",
            DOCS_DIR / "03-reference" / "index.md",
            DOCS_DIR / "03-reference" / "api-cli-and-packaging.md",
            DOCS_DIR / "04-explanation" / "index.md",
            DOCS_DIR / "04-explanation" / "kernel-port-allocation-and-race-model.md",
        ]
        for path in required:
            self.assertTrue(path.is_file(), f"Missing doc/module file: {path}")

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("wget wget", readme)
        self.assertNotIn("go get github.com/phayes/freeport", readme)
        self.assertIn('"log"', readme)
        self.assertIn("GetFreePorts", readme)

        for md_file in _iter_markdown():
            content = md_file.read_text(encoding="utf-8")
            plain = _strip_code(content)
            self.assertIsNone(FRENCH_MARKERS.search(plain), f"French marker found in {md_file}")
            for link in LINK_RE.findall(plain):
                if link.startswith(("http://", "https://", "mailto:")):
                    continue
                target_str, _, anchor = link.partition("#")
                target_path = md_file if not target_str else (md_file.parent / target_str).resolve()
                self.assertTrue(target_path.exists(), f"Broken link '{link}' in {md_file}")
                if anchor and target_path.is_file() and target_path.suffix == ".md":
                    slugs = _heading_slugs(target_path.read_text(encoding="utf-8"))
                    self.assertIn(anchor, slugs, f"Broken anchor '#{anchor}' in {md_file}")

        for howto in sorted((DOCS_DIR / "02-how-to-guides").glob("*.md")):
            plain = _strip_code(howto.read_text(encoding="utf-8"))
            self.assertIsNone(STE_BANNED.search(plain), f"ASD-STE100 banned pattern in {howto}")

    def test_mermaid_and_zero_ascii_diagrams(self) -> None:
        mermaid_total = 0
        for md_file in _iter_markdown():
            content = md_file.read_text(encoding="utf-8")
            for block in _extract_fenced_blocks(content):
                code = str(block["code"])
                info = str(block["info"])
                if info == "mermaid":
                    mermaid_total += 1
                    self.assertEqual(block["indent"], "", f"Indented mermaid fence in {md_file}")
                    first_line = next((ln.strip() for ln in code.splitlines() if ln.strip()), "")
                    self.assertTrue(
                        first_line.startswith(("flowchart ", "graph ", "sequenceDiagram")),
                        f"Unsupported mermaid diagram header '{first_line}' in {md_file}",
                    )
                elif info in {"", "text", "plaintext", "ascii"}:
                    self.assertNotIn("-->", code, f"ASCII arrow found in {md_file}")
                    self.assertNotIn("graph ", code, f"Untagged mermaid diagram in {md_file}")
                    self.assertIsNone(BOX_CHAR_RE.search(code), f"Box-drawing art in {md_file}")

        self.assertGreaterEqual(mermaid_total, 3)

    def test_go_module_tests_vet_fmt_and_bash_snippets(self) -> None:
        go_bin = shutil.which("go")
        self.assertIsNotNone(go_bin, "go toolchain not found in PATH")

        for cmd in (["go", "test", "-v", "./..."], ["go", "vet", "./..."]):
            res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(res.returncode, 0, f"{' '.join(cmd)} failed:\n{res.stdout}\n{res.stderr}")

        fmt_res = subprocess.run(
            ["gofmt", "-l", "docs_tutorials_howtos_test.go", "freeport.go", "freeport_test.go", "cmd/freeport/main.go"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(fmt_res.returncode, 0, fmt_res.stderr)
        self.assertEqual(fmt_res.stdout.strip(), "", f"Unformatted Go files:\n{fmt_res.stdout}")

        if os.name != "nt" and shutil.which("bash"):
            checked = 0
            for md_file in sorted(DOCS_DIR.rglob("*.md")):
                for block in _extract_fenced_blocks(md_file.read_text(encoding="utf-8")):
                    if str(block["info"]) in {"bash", "sh"}:
                        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, encoding="utf-8") as tmp:
                            tmp.write(str(block["code"]) + "\n")
                            tmp_path = tmp.name
                        try:
                            res = subprocess.run(["bash", "-n", tmp_path], capture_output=True, text=True, timeout=15)
                            self.assertEqual(res.returncode, 0, f"bash -n failed in {md_file}: {res.stderr}")
                            checked += 1
                        finally:
                            Path(tmp_path).unlink(missing_ok=True)
            self.assertGreaterEqual(checked, 4)


if __name__ == "__main__":
    unittest.main()
