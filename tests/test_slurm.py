"""Tests for parsing and editing SLURM batch files."""

from pathlib import Path

import pytest

import gdmate
from gdmate.slurm import SlurmScript

EXAMPLE = Path("scripts/server/stampede3/job_stampede3_2d.slurm")


def test_only_slurm_script_is_exposed_from_package():
    """Keep directive records as an implementation detail."""
    assert gdmate.SlurmScript is SlurmScript
    assert not hasattr(gdmate, "SlurmDirective")


def test_parse_and_write_without_edits_is_exact_round_trip(tmp_path):
    """Parsing and writing without edits preserves every character."""
    original = EXAMPLE.read_bytes()
    script = SlurmScript.from_file(EXAMPLE)
    output = tmp_path / "round_trip.slurm"

    script.write(output)

    assert output.read_bytes() == original


def test_parse_exposes_long_and_short_directives():
    """Both assignment and whitespace-separated directives are available."""
    script = SlurmScript.from_file(EXAMPLE)

    assert script.get_directive("--partition") == "skx"
    assert script.get_directive("-N") == "1"
    assert script.get_directive("--ntasks-per-node") == "48"
    assert script.get_directive("--time") == "48:00:00"


def test_header_edits_preserve_comments_formatting_and_body(tmp_path):
    """Only requested header values change; the body remains byte-for-byte."""
    script = SlurmScript.from_file(EXAMPLE)
    original_body = script.body

    script.set_directive("--partition", "spr")
    script.set_directive("-N", "2")
    script.set_directive("--job-name", "new_2d")
    output = tmp_path / "edited.slurm"
    script.write(output)

    edited = output.read_text()
    assert "#SBATCH --partition=spr         # Partition to submit the job" in edited
    assert "#SBATCH -N 2                         # Number of nodes" in edited
    assert "#SBATCH --job-name=new_2d   # Job name" in edited
    assert SlurmScript.from_file(output).body == original_body


def test_set_directive_rejects_unknown_key():
    """Accidental insertion is avoided unless the API explicitly supports it."""
    script = SlurmScript("#!/bin/bash\n#SBATCH --time=01:00:00\necho run\n")

    with pytest.raises(KeyError, match="--nodes"):
        script.set_directive("--nodes", "2")


def test_body_starts_after_last_header_directive_and_separator():
    """Comments belonging to the executable body are not treated as header."""
    script = SlurmScript.from_file(EXAMPLE)

    assert script.body.startswith("# Dealii and ASPECT DIR\n")
    assert script.body.endswith(
        "ibrun ${ASPECT_INSTALL_DIR}/build_master_TwoD_rebase/"
        "aspect-release ./case.prm\n"
    )


def test_parse_requires_a_slurm_directive():
    """A shell script without any SBATCH header is not a SLURM template."""
    with pytest.raises(ValueError, match="SBATCH"):
        SlurmScript("#!/bin/bash\necho run\n")
