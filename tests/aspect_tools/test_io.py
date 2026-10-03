"""Tests for ASPECT parameter-file input and output."""

from io import StringIO
from pathlib import Path

import pytest

from gdmate.aspect_tools.io import (
    parse_parameters_to_dict,
    save_parameters_from_dict,
)

DATA_DIR = Path(__file__).parents[1] / "data" / "aspect_tools"


def test_parse_parameters_to_dict():
    with (DATA_DIR / "test_parse_parameters_to_dict.prm").open() as stream:
        parameters = parse_parameters_to_dict(stream)

    assert parameters["Dimension"] == "2"
    assert parameters["Solver parameters"] == {
        "Stokes solver parameters": {"Linear solver tolerance": "1e-12"}
    }
    assert parameters["Geometry model"]["Spherical shell"] == {
        "Inner radius": "1",
        "Outer radius": "2",
        "Opening angle": "360",
    }
    multiline_value = parameters["Boundary velocity model"][
        "Prescribed velocity boundary indicators"
    ]
    assert multiline_value.splitlines() == [
        "bottom : AnnulusBoundary, \\",
        "                                                top : AnnulusBoundary",
    ]


def test_parse_convection_box_3d_cookbook():
    with (DATA_DIR / "convection_box_3d.prm").open() as stream:
        parameters = parse_parameters_to_dict(stream)

    assert parameters["Dimension"] == "3"
    assert parameters["Geometry model"]["Box"] == {
        "X extent": "1",
        "Y extent": "1",
        "Z extent": "1",
    }
    assert parameters["Mesh refinement"] == {
        "Initial global refinement": "3",
        "Initial adaptive refinement": "3",
        "Time steps between mesh refinement": "15",
        "Additional refinement times": "0.003",
    }


def test_repeated_subsection_merging():
    stream = StringIO(
        """
subsection A
  set x = 1
end

subsection A
  set y = 2
end
"""
    )

    assert parse_parameters_to_dict(stream) == {"A": {"x": "1", "y": "2"}}


def test_save_parameters_from_dict(tmp_path):
    parameters = {
        "Dimension": "2",
        "Solver parameters": {
            "Stokes solver parameters": {"Linear solver tolerance": "1e-12"}
        },
        "Geometry model": {
            "Spherical shell": {
                "Inner radius": "1",
                "Outer radius": "2",
                "Opening angle": "360",
            }
        },
    }
    output_path = tmp_path / "test_output.prm"

    with output_path.open("w") as stream:
        save_parameters_from_dict(stream, parameters)

    assert output_path.read_text() == (
        DATA_DIR / "test_save_parameters_from_dict_expected.prm"
    ).read_text()


def test_save_parameters_from_dict_custom_indent_width():
    output = StringIO()

    save_parameters_from_dict(
        output,
        {"Outer": {"Inner": {"Value": "1"}}},
        indent_width=2,
    )

    assert output.getvalue() == (
        "\nsubsection Outer\n"
        "  subsection Inner\n"
        "    set Value = 1\n"
        "  end\n"
        "end\n"
    )


def test_save_parameters_from_dict_with_include_path():
    output = StringIO()

    save_parameters_from_dict(
        output,
        {
            "Mesh refinement": {
                "Initial global refinement": "4",
                "Initial adaptive refinement": "4",
            }
        },
        include_path="convection_box_3d.prm",
    )

    assert output.getvalue() == (
        "include convection_box_3d.prm\n"
        "\nsubsection Mesh refinement\n"
        "    set Initial global refinement = 4\n"
        "    set Initial adaptive refinement = 4\n"
        "end\n"
    )


def test_save_parameters_invalid_value_type_raises():
    with pytest.raises(ValueError, match="must be str or dict"):
        save_parameters_from_dict(StringIO(), {"invalid": 123})
