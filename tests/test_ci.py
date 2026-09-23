"""Tests for continuous-integration configuration."""

from pathlib import Path


def test_ci_discovers_all_notebooks():
    """The notebook check should discover every notebook in the directory."""
    repository_root = Path(__file__).parents[1]
    workflow = (repository_root / ".github/workflows/python-test.yml").read_text(
        encoding="utf-8"
    )

    assert "run: pytest --nbmake notebooks\n" in workflow


def test_ci_installs_pandoc_for_documentation():
    """The documentation job should provide Pandoc for nbsphinx."""
    repository_root = Path(__file__).parents[1]
    workflow = (repository_root / ".github/workflows/python-test.yml").read_text(
        encoding="utf-8"
    )

    assert "uses: pandoc/actions/setup@v1\n" in workflow
