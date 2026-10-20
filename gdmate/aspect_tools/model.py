"""High-level parser for the files in an ASPECT model output directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from gdmate.aspect_tools.io import parse_parameters_to_dict
from gdmate.aspect_tools.log import AspectLogParser, AspectTimestep, AspectTimingBlock


class AspectModelParser:
    """Collect model parameters, timesteps, and timing tables.

    Parameters
    ----------
    model_directory
        Directory containing the ASPECT model.
    output_directory
        Output directory, relative to ``model_directory`` or absolute. Defaults
        to ``"output"``; no input parameter file is consulted to discover it.
    validate_version
        Forwarded to :class:`AspectLogParser`. By default, logs must report
        ASPECT major version 3.

    Notes
    -----
    Call :meth:`parse` to load ``log.txt``, ``original.prm``, and
    ``parameters.json`` from the output directory. ``original.wb`` is optional.
    JSON files must contain objects. Parameters are stored as read, without
    flattening or converting values. Log records retain their original units,
    file order, and repeated timestep numbers (for example, after a restart).
    Repeated calls replace previously collected data. A failed parse leaves
    previously collected data intact.
    """

    def __init__(
        self,
        model_directory: Union[str, Path],
        output_directory: Union[str, Path] = "output",
        validate_version: bool = True,
    ) -> None:
        self.model_directory = Path(model_directory).resolve()
        output = Path(output_directory)
        self.output_directory = (
            output if output.is_absolute() else self.model_directory / output
        )
        self.validate_version = validate_version
        self.original_parameters: dict = {}
        self.parameters: dict = {}
        self.world_builder_parameters: Optional[dict] = None
        self.timesteps: list[AspectTimestep] = []
        self.timing_blocks: list[AspectTimingBlock] = []

    def parse(self) -> None:
        """Read model output files and replace the stored dictionaries and records.

        Missing required files raise ``FileNotFoundError``. Invalid content
        raises ``ValueError`` with the source path. An absent ``original.wb``
        sets ``world_builder_parameters`` to ``None``.
        """
        prm_path = self.output_directory / "original.prm"
        with prm_path.open(encoding="utf-8") as stream:
            try:
                original_parameters = parse_parameters_to_dict(stream)
            except ValueError as error:
                raise ValueError(f"{prm_path}: {error}") from error

        parameters = self._read_json(self.output_directory / "parameters.json")
        wb_path = self.output_directory / "original.wb"
        try:
            world_builder_parameters = self._read_json(wb_path)
        except FileNotFoundError:
            world_builder_parameters = None

        log_parser = AspectLogParser(
            self.output_directory / "log.txt",
            validate_version=self.validate_version,
        )
        timesteps = log_parser.parse()
        timing_blocks = log_parser.parse_timing_blocks()

        self.original_parameters = original_parameters
        self.parameters = parameters
        self.world_builder_parameters = world_builder_parameters
        self.timesteps = timesteps
        self.timing_blocks = timing_blocks

    @staticmethod
    def _read_json(path: Path) -> dict:
        with path.open(encoding="utf-8") as stream:
            try:
                parameters = json.load(stream)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}: {error}") from error
        if not isinstance(parameters, dict):
            raise ValueError(f"{path}: expected a JSON object")
        return parameters
