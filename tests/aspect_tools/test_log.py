"""Tests for parsing ASPECT log files."""

from pathlib import Path

import pytest

from gdmate.aspect_tools.log import (
    AspectLogParser,
    AspectTimestep,
    AspectTimingBlock,
    AspectTimingSection,
    UnsupportedAspectVersionError,
)

DATA_DIR = Path(__file__).parents[1] / "data" / "aspect_tools"


def write_log(tmp_path: Path, contents: str) -> Path:
    """Write a small ASPECT log fixture and return its path."""
    path = tmp_path / "log.txt"
    path.write_text(contents)
    return path


def test_iter_timesteps_parses_records_in_one_pass(tmp_path):
    path = write_log(
        tmp_path,
        """ASPECT header
*** Timestep 0:  t=0 years, dt=0 years
solver output
*** Timestep 1:  t=1.25e+03 years, dt=1.25e+03 years
""",
    )

    records = list(
        AspectLogParser(path, validate_version=False).iter_timesteps()
    )

    assert records == [
        AspectTimestep(0, 0.0, 0.0, "years", 2),
        AspectTimestep(1, 1250.0, 1250.0, "years", 4),
    ]


def test_parser_is_iterable_and_parse_collects_records(tmp_path):
    path = write_log(
        tmp_path,
        "  *** Timestep 7: t=2.5 seconds, dt=0.5 seconds\n",
    )
    parser = AspectLogParser(path, validate_version=False)

    expected = [AspectTimestep(7, 2.5, 0.5, "seconds", 1)]
    assert list(parser) == expected
    assert parser.parse() == expected


def test_malformed_timestep_header_reports_source_line(tmp_path):
    path = write_log(tmp_path, "header\n*** Timestep malformed\n")

    with pytest.raises(ValueError, match=r"log\.txt:2: malformed timestep header"):
        list(AspectLogParser(path, validate_version=False))


def test_mismatched_time_units_are_rejected(tmp_path):
    path = write_log(
        tmp_path,
        "*** Timestep 1: t=1 years, dt=1 seconds\n",
    )

    with pytest.raises(ValueError, match="time and timestep units differ"):
        list(AspectLogParser(path, validate_version=False))


def test_parse_timing_block_and_associate_latest_timestep(tmp_path):
    path = write_log(
        tmp_path,
        """*** Timestep 4: t=100 years, dt=25 years
+----------------------+-----------+-----------+
| Total wallclock time elapsed since start | 6.31e+03s | |
|                                          |           | |
| Section                    | no. calls | wall time | % of total |
+----------------------------+-----------+-----------+------------+
| Execute FastScape          |       200 |  3.3e+03s |        52% |
| Particles: Initialization  |         1 | 0.000248s |         0% |
+----------------------------+-----------+-----------+------------+
""",
    )

    blocks = AspectLogParser(path, validate_version=False).parse_timing_blocks()

    assert blocks == [
        AspectTimingBlock(
            total_wallclock_seconds=6310.0,
            sections=(
                AspectTimingSection("Execute FastScape", 200, 3300.0, 52.0),
                AspectTimingSection(
                    "Particles: Initialization", 1, 0.000248, 0.0
                ),
            ),
            line_number=3,
            timestep_number=4,
        )
    ]


def test_iter_timing_blocks_finds_multiple_run_summaries(tmp_path):
    table = """| Total wallclock time elapsed since start | {total}s | |
| Section | no. calls | wall time | % of total |
+---------+-----------+-----------+------------+
| {name}  | {calls} | {wall}s | {percent}% |
+---------+-----------+-----------+------------+
"""
    path = write_log(
        tmp_path,
        table.format(
            total="10",
            name="Initialization",
            calls="1",
            wall="2",
            percent="20",
        )
        + "*** Timestep 8: t=80 years, dt=10 years\n"
        + table.format(
            total="2e+01", name="Solve Stokes system", calls="4", wall="5", percent="25"
        ),
    )

    blocks = list(
        AspectLogParser(path, validate_version=False).iter_timing_blocks()
    )

    assert [block.total_wallclock_seconds for block in blocks] == [10.0, 20.0]
    assert [block.timestep_number for block in blocks] == [None, 8]


def test_malformed_timing_row_reports_source_line(tmp_path):
    path = write_log(
        tmp_path,
        """| Total wallclock time elapsed since start | 10s | |
| Section | no. calls | wall time | % of total |
+---------+-----------+-----------+------------+
| Solve Stokes system | not-a-number | 5s | 50% |
+---------+-----------+-----------+------------+
""",
    )

    with pytest.raises(ValueError, match=r"log\.txt:4: malformed timing row"):
        list(
            AspectLogParser(path, validate_version=False).iter_timing_blocks()
        )


def test_truncated_timing_block_is_rejected(tmp_path):
    path = write_log(
        tmp_path,
        """| Total wallclock time elapsed since start | 10s | |
| Section | no. calls | wall time | % of total |
+---------+-----------+-----------+------------+
| Initialization | 1 | 2s | 20% |
""",
    )

    with pytest.raises(ValueError, match="unterminated timing block"):
        list(
            AspectLogParser(path, validate_version=False).iter_timing_blocks()
        )


def test_parse_version_from_aspect_header(tmp_path):
    path = write_log(
        tmp_path,
        """--     . version 3.1.0-pre (main, abc123)
*** Timestep 0: t=0 years, dt=0 years
""",
    )
    parser = AspectLogParser(path)

    assert parser.version == "3.1.0-pre"
    assert parser.major_version == 3
    assert len(parser.parse()) == 1


def test_unsupported_major_version_is_rejected_before_records(tmp_path):
    path = write_log(
        tmp_path,
        """--     . version 2.6.0
*** Timestep malformed
""",
    )

    with pytest.raises(
        UnsupportedAspectVersionError,
        match=r"ASPECT major version 3 is required; found 2\.6\.0",
    ):
        list(AspectLogParser(path))


def test_version_validation_can_be_disabled(tmp_path):
    path = write_log(
        tmp_path,
        """--     . version 2.6.0
*** Timestep 2: t=10 years, dt=5 years
""",
    )

    records = AspectLogParser(path, validate_version=False).parse()

    assert records == [AspectTimestep(2, 10.0, 5.0, "years", 2)]


def test_missing_version_is_rejected_by_default(tmp_path):
    path = write_log(
        tmp_path,
        "*** Timestep 0: t=0 years, dt=0 years\n",
    )

    with pytest.raises(ValueError, match="ASPECT version header not found"):
        AspectLogParser(path).parse()


def test_repository_fixture_contains_two_real_timing_blocks():
    path = DATA_DIR / "aspect_log_with_timing_blocks.txt"
    parser = AspectLogParser(path)

    assert [record.number for record in parser.parse()] == [100, 200]

    blocks = parser.parse_timing_blocks()
    assert [block.timestep_number for block in blocks] == [100, 200]
    assert [block.total_wallclock_seconds for block in blocks] == [3190.0, 6310.0]
    assert [len(block.sections) for block in blocks] == [27, 27]
