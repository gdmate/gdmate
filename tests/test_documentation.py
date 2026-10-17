"""Tests for the documentation configuration."""

import os
import runpy
import shutil
from pathlib import Path


def test_sphinx_configuration_uses_repository_relative_paths(tmp_path):
    """The Sphinx configuration should not depend on the current directory."""
    repository_root = Path(__file__).parents[1]
    temporary_repository = tmp_path / "repository"
    temporary_docs = temporary_repository / "docs"
    temporary_notebooks = temporary_repository / "notebooks"
    temporary_docs.mkdir(parents=True)
    temporary_notebooks.mkdir()
    (temporary_notebooks / "example.ipynb").write_text("notebook", encoding="utf-8")
    shutil.copy2(repository_root / "docs" / "conf.py", temporary_docs / "conf.py")

    previous_directory = Path.cwd()
    unrelated_directory = tmp_path / "unrelated"
    unrelated_directory.mkdir()
    try:
        os.chdir(unrelated_directory)
        runpy.run_path(temporary_docs / "conf.py")
    finally:
        os.chdir(previous_directory)

    assert (temporary_docs / "notebooks" / "example.ipynb").is_file()


def test_readme_documents_environment_setup():
    """The README should link dependencies and provide setup commands."""
    repository_root = Path(__file__).parents[1]
    readme = (repository_root / "README.md").read_text(encoding="utf-8")

    assert (
        "[pyproject.toml](https://github.com/gdmate/gdmate/blob/main/pyproject.toml)"
        in readme
    )
    assert "conda create --name py-gdmate python=3.13 pip" in readme
    assert "For ordinary users" in readme
    assert "python -m pip install ." in readme
    assert "runtime dependencies" in readme
    assert "For contributors" in readme
    assert 'python -m pip install -e ".[dev,docs]"' in readme
    assert "development and documentation dependencies" in readme
