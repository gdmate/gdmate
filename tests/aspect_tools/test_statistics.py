"""Tests for parsing ASPECT statistics files."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gdmate.aspect_tools import AspectStatistics

DATA_DIR = Path(__file__).parents[1] / "data" / "aspect_tools"


def write_statistics(tmp_path, contents):
    path = tmp_path / "statistics"
    path.write_text(contents, encoding="utf-8")
    return path


def test_parse_real_statistics_excerpt():
    path = DATA_DIR / "statistics_excerpt.txt"
    statistics = AspectStatistics(path)

    assert path.stat().st_size < 100_000
    assert isinstance(statistics.data, pd.DataFrame)
    assert statistics.data.shape == (20, 43)
    assert tuple(statistics.data.columns[:3]) == (
        "Time step number",
        "Time",
        "Time step size",
    )
    assert tuple(statistics.data.columns[-2:]) == (
        "Minimum topography",
        "Maximum topography",
    )
    assert statistics.units["Time step number"] is None
    assert statistics.units["Time"] == "years"
    assert statistics.units["Time step size"] == "years"
    assert statistics.units["Average viscosity"] == "Pa s"
    assert statistics.units["Maximum topography"] == "m"
    np.testing.assert_array_equal(
        statistics.data["Time step number"], np.arange(20)
    )
    assert statistics.data["Time step number"].dtype == np.dtype(np.int64)
    assert statistics.data["Time"].dtype == np.dtype(np.float64)
    assert statistics.data["Time"][1] == pytest.approx(82.54928668369)
    assert statistics.data["Visualization file name"][0] == (
        "output/solution/solution-00000"
    )
    assert statistics.data["Visualization file name"][1] == ""
    assert statistics.data["Particle file name"][0] == (
        "output/particles/particles-00000"
    )
    assert statistics.data.loc[1, "Visualization file name"] == ""


def test_quoted_string_with_spaces(tmp_path):
    path = write_statistics(
        tmp_path,
        """# 1: Time step number
# 2: Output file
0 "output/a file"
1 ""
""",
    )

    statistics = AspectStatistics(path)

    np.testing.assert_array_equal(statistics.data["Time step number"], [0, 1])
    np.testing.assert_array_equal(
        statistics.data["Output file"], ["output/a file", ""]
    )
    assert statistics.units == {"Time step number": None, "Output file": None}


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("0 1\n", r"statistics:1: data row precedes column definitions"),
        (
            "# 2: Time\n0\n",
            r"statistics:1: expected column 1, found column 2",
        ),
        (
            "# 1: Time\n# 2: Time\n0 1\n",
            r"statistics:2: duplicate column name 'Time'",
        ),
        (
            "# 1: Step\n# 2: Time\n0\n",
            r"statistics:3: expected 2 values, found 1",
        ),
        (
            '# 1: File\n"unterminated\n',
            r"statistics:2: malformed quoted value",
        ),
        (
            "# 1: Step\n0\n# 2: Time\n",
            r"statistics:3: column definition follows data rows",
        ),
    ],
)
def test_malformed_statistics_reports_source_line(tmp_path, contents, message):
    path = write_statistics(tmp_path, contents)

    with pytest.raises(ValueError, match=message):
        AspectStatistics(path)


def test_file_without_numbered_columns_is_rejected(tmp_path):
    path = write_statistics(tmp_path, "# ASPECT statistics\n")

    with pytest.raises(ValueError, match=r"statistics: no statistics columns found"):
        AspectStatistics(path)


def test_duplicate_names_after_removing_units_are_rejected(tmp_path):
    path = write_statistics(
        tmp_path,
        "# 1: Time (years)\n# 2: Time (seconds)\n0 0\n",
    )

    with pytest.raises(ValueError, match=r"statistics:2: duplicate column name 'Time'"):
        AspectStatistics(path)
