"""Tests for the model-level ASPECT parser."""

import json
from pathlib import Path

import pytest

from gdmate.aspect_tools import AspectModelParser, AspectTimestep

DATA_DIR = Path(__file__).parents[1] / "data" / "aspect_tools"


@pytest.fixture
def model_dir(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "log.txt").write_text(
        (DATA_DIR / "aspect_log_with_timing_blocks.txt").read_text()
    )
    (output / "original.prm").write_text(
        "set Dimension = 2\nsubsection Geometry model\n"
        "  set Model name = box\nend\n"
    )
    (output / "parameters.json").write_text(json.dumps({"Dimension": "2"}))
    return tmp_path


def test_parse_model_files(model_dir):
    parser = AspectModelParser(model_dir)
    parser.parse()

    assert parser.output_directory == model_dir / "output"
    assert parser.original_parameters == {
        "Dimension": "2", "Geometry model": {"Model name": "box"}
    }
    assert parser.parameters == {"Dimension": "2"}
    assert parser.world_builder_parameters is None
    assert [step.number for step in parser.timesteps] == [100, 200]
    assert all(isinstance(step, AspectTimestep) for step in parser.timesteps)
    assert parser.timesteps[0].time_unit == "years"
    assert [block.timestep_number for block in parser.timing_blocks] == [100, 200]


@pytest.mark.parametrize("absolute", [False, True])
def test_custom_output_directory(model_dir, tmp_path, monkeypatch, absolute):
    output = model_dir / "custom-output"
    (model_dir / "output").rename(output)
    monkeypatch.chdir(model_dir.parent)
    parser = AspectModelParser(
        model_dir, output_directory=output if absolute else "custom-output"
    )
    parser.parse()
    assert parser.output_directory == output
    assert len(parser.timesteps) == 2


def test_world_builder_and_reparse_replace_records(model_dir):
    output = model_dir / "output"
    settings = {"version": "1.0", "features": []}
    (output / "original.wb").write_text(json.dumps(settings))
    parser = AspectModelParser(model_dir)
    parser.parse()
    assert parser.world_builder_parameters == settings
    (output / "original.wb").unlink()
    parser.parse()
    assert parser.world_builder_parameters is None
    assert len(parser.timesteps) == 2


def test_repeated_timesteps_are_preserved(model_dir):
    (model_dir / "output" / "log.txt").write_text(
        "*** Timestep 1: t=10 seconds, dt=10 seconds\n"
        "*** Timestep 1: t=12 seconds, dt=12 seconds\n"
    )
    parser = AspectModelParser(model_dir, validate_version=False)
    parser.parse()
    assert [step.number for step in parser.timesteps] == [1, 1]
    assert [step.time for step in parser.timesteps] == [10, 12]
    assert parser.timing_blocks == []


@pytest.mark.parametrize("filename", ["log.txt", "original.prm", "parameters.json"])
def test_missing_required_file(model_dir, filename):
    (model_dir / "output" / filename).unlink()
    with pytest.raises(FileNotFoundError, match=filename):
        AspectModelParser(model_dir).parse()


@pytest.mark.parametrize("filename", ["parameters.json", "original.wb"])
@pytest.mark.parametrize("contents", ["{invalid", "[]"])
def test_invalid_json_reports_path(model_dir, filename, contents):
    (model_dir / "output" / filename).write_text(contents)
    with pytest.raises(ValueError, match=filename):
        AspectModelParser(model_dir).parse()


def test_invalid_prm_reports_path(model_dir):
    (model_dir / "output" / "original.prm").write_text("set invalid\n")
    with pytest.raises(ValueError, match="original.prm"):
        AspectModelParser(model_dir).parse()


def test_version_validation_is_enabled_by_default(model_dir):
    (model_dir / "output" / "log.txt").write_text(
        "-- . version 2.6.0\n*** Timestep 0: t=0 years, dt=0 years\n"
    )
    with pytest.raises(ValueError, match="major version 3 is required"):
        AspectModelParser(model_dir).parse()


def test_failed_refresh_keeps_previous_data(model_dir):
    parser = AspectModelParser(model_dir)
    parser.parse()
    previous_timesteps = parser.timesteps
    previous_parameters = parser.parameters
    (model_dir / "output" / "parameters.json").write_text('{"Dimension": "3"}')
    (model_dir / "output" / "log.txt").write_text(
        "-- . version 3.1.0\n*** Timestep malformed\n"
    )
    with pytest.raises(ValueError, match="malformed timestep header"):
        parser.parse()
    assert parser.timesteps is previous_timesteps
    assert parser.parameters is previous_parameters
