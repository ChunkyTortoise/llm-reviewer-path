import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_replay() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "receipts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_replay_module_shows_scores_approval_flow_and_updated_contact() -> None:
    lines = _run_replay().splitlines()
    assert "GOOD: score=1.00, n=5, gate=True" in lines
    assert "MUTATION: score=0.80, n=5, gate=False" in lines
    assert "without token: denied_without_approval" in lines
    assert "model text: ApprovalError untrusted approval" in lines
    assert "approved: execute_once" in lines
    assert "retry: duplicate_retry_suppressed" in lines
    assert lines[-1] == "read after: {'ok': True, 'name': 'Ada', 'city': 'LA'}"
    assert not any("tok_" in line for line in lines)


def test_replay_output_matches_documented_output() -> None:
    doc = (ROOT / "docs" / "offline-receipt.md").read_text()
    readme = (ROOT / "README.md").read_text()
    block = re.search(r"Actual output.*?```text\n(.*?)```", doc, re.S)
    readme_block = re.search(
        r"Exact output of <code>uv run python -m receipts</code>.*?\n```text\n(.*?)```",
        readme,
        re.S,
    )
    assert block is not None
    assert readme_block is not None
    replay_stdout = _run_replay()
    assert replay_stdout == block.group(1)
    assert replay_stdout == readme_block.group(1)

    _validate_local_links(readme)

    mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", readme, re.S)
    assert len(mermaid_blocks) == 2
    for m_block in mermaid_blocks:
        m_lines = [ln.strip() for ln in m_block.strip().splitlines() if ln.strip()]
        assert m_lines[0].startswith(("sequenceDiagram", "flowchart"))
        assert sum(1 for ln in m_lines if ln.startswith("subgraph ")) == sum(
            1 for ln in m_lines if ln == "end"
        )


class _HTMLLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src"} and value is not None:
                self.targets.append(value)


def _heading_ids(markdown: str) -> set[str]:
    # GitHub slugs for the plain-text headings used in these documents.
    return {
        re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
        for heading in re.findall(r"^#{1,6} +(.+)$", markdown, re.M)
    }


def _validate_local_links(readme: str) -> None:
    html = _HTMLLinks()
    html.feed(readme)
    targets = re.findall(r"\]\(([^)]+)\)", readme) + html.targets
    for raw_target in targets:
        target = urlsplit(raw_target)
        if target.scheme or target.netloc:
            continue
        rel_path = unquote(target.path)
        target_path = ROOT / rel_path if rel_path else ROOT / "README.md"
        assert target_path.exists(), f"Missing README link target: {raw_target}"
        if not target.fragment:
            continue
        assert target_path.is_file(), f"Anchor on non-file: {raw_target}"
        fragment = unquote(target.fragment)
        line_match = re.fullmatch(r"L(\d+)(?:-L(\d+))?", fragment)
        text = readme if target_path == ROOT / "README.md" else target_path.read_text()
        if line_match:
            end_line = int(line_match.group(2) or line_match.group(1))
            assert 1 <= int(line_match.group(1)) <= end_line <= len(text.splitlines()), raw_target
        else:
            assert fragment in _heading_ids(text), f"Missing README heading: {raw_target}"


def test_readme_local_links() -> None:
    _validate_local_links((ROOT / "README.md").read_text())


def test_readme_rejects_broken_links(monkeypatch: pytest.MonkeyPatch) -> None:
    original = Path.read_text
    readme = (ROOT / "README.md").read_text()
    mutations = [
        ('src="./docs/assets/terminal-demo.gif"', 'src="./docs/assets/missing.gif"'),
        ('href="docs/demo.tape"', 'href="docs/missing.tape"'),
        ('](#results)', '](#missing-heading)'),
        ('docs/offline-receipt.md#visual-asset-provenance', 'docs/offline-receipt.md#missing'),
        ('gate.py#L6)', 'gate.py#L9999)'),
        ('](LICENSE)', '](MISSING-LICENSE)'),
    ]
    for before, after in mutations:
        assert before in readme
        with pytest.raises(AssertionError):
            _validate_local_links(readme.replace(before, after))

    def read_with_missing_asset(path: Path, *args: object, **kwargs: object) -> str:
        if path == ROOT / "README.md":
            return readme.replace(*mutations[0])
        return original(path)

    monkeypatch.setattr(Path, "read_text", read_with_missing_asset)
    with pytest.raises(AssertionError):
        test_replay_output_matches_documented_output()
