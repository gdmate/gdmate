"""Tests for the public package layout."""

import gdmate as gd
import gdmate.analysis
import gdmate.aspect_tools
from gdmate.rheology_models import rheology


def test_rheology_module_uses_renamed_package():
    """The public rheology module comes from the renamed subpackage."""
    assert gd.rheology is rheology


def test_empty_subpackages_use_renamed_layout():
    """The renamed analysis and ASPECT-tool packages are importable."""
    assert gdmate.analysis.__name__ == "gdmate.analysis"
    assert gdmate.aspect_tools.__name__ == "gdmate.aspect_tools"
