"""Streaming parser for ASPECT log files."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Tuple, Union

_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_TIMESTEP_PATTERN = re.compile(
    rf"^\s*\*{{3}}\s+Timestep\s+(?P<number>\d+):\s*"
    rf"t=(?P<time>{_NUMBER})\s+(?P<time_unit>\S+),\s*"
    rf"dt=(?P<timestep_size>{_NUMBER})\s+(?P<timestep_unit>\S+)\s*$"
)
_TOTAL_WALLCLOCK_PATTERN = re.compile(
    rf"^\s*\|\s*Total wallclock time elapsed since start\s*"
    rf"\|\s*(?P<seconds>{_NUMBER})s\s*\|.*$"
)
_SECONDS_PATTERN = re.compile(rf"^(?P<value>{_NUMBER})s$")
_PERCENT_PATTERN = re.compile(rf"^(?P<value>{_NUMBER})%$")
_VERSION_PATTERN = re.compile(
    r"^\s*--\s+\.\s+version\s+(?P<version>\S+)"
)
_SOLVER_OUTPUT_PATTERN = re.compile(
    r"^\s*Solving\s+(?P<system>.+?)\s+system\s*"
    r"(?:\((?P<solver>[^)]+)\))?\s*\.\.\.\s*"
    r"(?P<iterations>\d+(?:\+\d+)*)\s+iterations\.\s*$"
)
_SKIPPED_SOLVER_PATTERN = re.compile(
    r"^\s*Skipping\s+(?P<system>.+?)\s+composition solve "
    r"because RHS is zero\.\s*$"
)
_FAILED_SOLVER_PATTERN = re.compile(
    r"^\s*linear solver failed(?:\s+\((?P<solver>[^)]+)\))?,\s*"
    r"continuing\s*$"
)


class UnsupportedAspectVersionError(ValueError):
    """Raised when an ASPECT log has an unsupported major version."""


@dataclass(frozen=True)
class AspectTimestep:
    """A timestep header parsed from an ASPECT log."""

    number: int
    time: float
    timestep_size: float
    time_unit: str
    line_number: int


@dataclass(frozen=True)
class AspectSolverOutput:
    """One linear-solver result associated with an ASPECT timestep."""

    timestep: AspectTimestep
    system: str
    solver: Optional[str]
    iteration_counts: Tuple[int, ...]
    status: str
    line_number: int


@dataclass(frozen=True)
class AspectTimingSection:
    """One section row from an ASPECT wall-clock timing table."""

    name: str
    call_count: int
    wall_time_seconds: float
    percent_of_total: float


@dataclass(frozen=True)
class AspectTimingBlock:
    """An ASPECT wall-clock timing table and its run context."""

    total_wallclock_seconds: float
    sections: Tuple[AspectTimingSection, ...]
    line_number: int
    timestep_number: Optional[int]


class AspectLogParser:
    """Parse structured records from an ASPECT log without loading it in memory.

    Parameters
    ----------
    path
        Path to an ASPECT standard-output log.
    validate_version
        Require an ASPECT major version 3 header before parsing records. Set
        this to ``False`` when deliberately parsing a log fragment or an older
        ASPECT log.
    """

    def __init__(
        self, path: Union[str, Path], validate_version: bool = True
    ) -> None:
        self.path = Path(path)
        self.validate_version = validate_version
        self._version: Optional[str] = None
        self._major_version: Optional[int] = None

    @property
    def version(self) -> str:
        """Return the ASPECT version string reported in the log header."""
        self._read_version()
        assert self._version is not None
        return self._version

    @property
    def major_version(self) -> int:
        """Return the major component of the ASPECT version."""
        self._read_version()
        assert self._major_version is not None
        return self._major_version

    def __iter__(self) -> Iterator[AspectTimestep]:
        """Iterate over timestep records in file order."""
        return self.iter_timesteps()

    def iter_timesteps(self) -> Iterator[AspectTimestep]:
        """Yield timestep records while streaming through the log once."""
        self._validate_supported_version()
        with self.path.open(encoding="utf-8", errors="replace") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.lstrip().startswith("*** Timestep"):
                    continue
                yield self._parse_timestep(line, line_number)

    def parse(self) -> List[AspectTimestep]:
        """Collect and return all timestep records from the log."""
        return list(self.iter_timesteps())

    def iter_solver_outputs(self) -> Iterator[AspectSolverOutput]:
        """Yield solved, skipped, and failed linear-solver records.

        A timestep can contain multiple records for the same system when an
        outer nonlinear solver repeats its linear solves. Compound counts such
        as ``200+0 iterations`` are retained as a tuple. A restarted log can
        contain repeated timestep numbers; records therefore carry the full
        :class:`AspectTimestep` rather than only its number.
        """
        self._validate_supported_version()
        latest_timestep = None
        pending_output = None

        with self.path.open(encoding="utf-8", errors="replace") as stream:
            for line_number, line in enumerate(stream, start=1):
                if line.lstrip().startswith("*** Timestep"):
                    if pending_output is not None:
                        yield pending_output
                        pending_output = None
                    latest_timestep = self._parse_timestep(line, line_number)
                    continue

                if _VERSION_PATTERN.match(line) is not None:
                    if pending_output is not None:
                        yield pending_output
                        pending_output = None
                    latest_timestep = None
                    continue

                solve_match = _SOLVER_OUTPUT_PATTERN.fullmatch(line)
                skipped_match = _SKIPPED_SOLVER_PATTERN.fullmatch(line)
                failed_match = _FAILED_SOLVER_PATTERN.fullmatch(line)

                if failed_match is not None:
                    if pending_output is None:
                        raise self._parse_error(
                            line_number, "solver failure without a solver record"
                        )
                    failed_solver = failed_match.group("solver")
                    if (
                        failed_solver is not None
                        and pending_output.solver != failed_solver
                    ):
                        raise self._parse_error(
                            line_number,
                            "solver failure does not match preceding solver",
                        )
                    yield replace(pending_output, status="failed")
                    pending_output = None
                    continue

                if solve_match is not None or skipped_match is not None:
                    if pending_output is not None:
                        yield pending_output
                    if latest_timestep is None:
                        raise self._parse_error(
                            line_number, "solver output precedes the first timestep"
                        )

                    if solve_match is not None:
                        pending_output = AspectSolverOutput(
                            timestep=latest_timestep,
                            system=solve_match.group("system"),
                            solver=solve_match.group("solver"),
                            iteration_counts=tuple(
                                int(value)
                                for value in solve_match.group("iterations").split("+")
                            ),
                            status="solved",
                            line_number=line_number,
                        )
                    else:
                        assert skipped_match is not None
                        pending_output = AspectSolverOutput(
                            timestep=latest_timestep,
                            system=skipped_match.group("system"),
                            solver=None,
                            iteration_counts=(),
                            status="skipped",
                            line_number=line_number,
                        )
                    continue

                if pending_output is not None:
                    yield pending_output
                    pending_output = None

                if line.lstrip().startswith("Solving") and "system" in line:
                    if "---" in line:
                        latest_timestep = None
                        continue
                    raise self._parse_error(
                        line_number, "malformed solver output record"
                    )

            if pending_output is not None:
                yield pending_output

    def parse_solver_outputs(self) -> List[AspectSolverOutput]:
        """Collect and return all linear-solver records from the log."""
        return list(self.iter_solver_outputs())

    def iter_timing_blocks(self) -> Iterator[AspectTimingBlock]:
        """Yield wall-clock timing tables while streaming through the log."""
        self._validate_supported_version()
        latest_timestep = None
        block_line_number = None
        total_wallclock_seconds = None
        sections: List[AspectTimingSection] = []
        state = "search"

        with self.path.open(encoding="utf-8", errors="replace") as stream:
            for line_number, line in enumerate(stream, start=1):
                if line.lstrip().startswith("*** Timestep"):
                    latest_timestep = self._parse_timestep(line, line_number).number

                total_match = _TOTAL_WALLCLOCK_PATTERN.fullmatch(
                    line.rstrip("\r\n")
                )
                if total_match is not None:
                    if state != "search":
                        raise self._parse_error(
                            line_number, "new timing block before previous block ended"
                        )
                    block_line_number = line_number
                    total_wallclock_seconds = float(total_match.group("seconds"))
                    sections = []
                    state = "header"
                    continue

                if state == "header":
                    if line.lstrip().startswith("| Section"):
                        state = "header_separator"
                    continue

                if state == "header_separator":
                    if self._is_table_separator(line):
                        state = "rows"
                    continue

                if state == "rows":
                    if self._is_table_separator(line):
                        assert block_line_number is not None
                        assert total_wallclock_seconds is not None
                        yield AspectTimingBlock(
                            total_wallclock_seconds=total_wallclock_seconds,
                            sections=tuple(sections),
                            line_number=block_line_number,
                            timestep_number=latest_timestep,
                        )
                        block_line_number = None
                        total_wallclock_seconds = None
                        sections = []
                        state = "search"
                        continue

                    if line.lstrip().startswith("|"):
                        sections.append(self._parse_timing_section(line, line_number))

        if state != "search":
            assert block_line_number is not None
            raise self._parse_error(block_line_number, "unterminated timing block")

    def parse_timing_blocks(self) -> List[AspectTimingBlock]:
        """Collect and return all wall-clock timing tables from the log."""
        return list(self.iter_timing_blocks())

    def _read_version(self) -> None:
        if self._version is not None:
            return

        with self.path.open(encoding="utf-8", errors="replace") as stream:
            for line_number, line in enumerate(stream, start=1):
                match = _VERSION_PATTERN.match(line)
                if match is None:
                    continue

                version = match.group("version")
                major_match = re.match(r"(?P<major>\d+)(?:\.|$)", version)
                if major_match is None:
                    raise self._parse_error(
                        line_number, f"malformed ASPECT version {version!r}"
                    )

                self._version = version
                self._major_version = int(major_match.group("major"))
                return

        raise ValueError(f"{self.path}: ASPECT version header not found")

    def _validate_supported_version(self) -> None:
        if not self.validate_version:
            return

        if self.major_version != 3:
            raise UnsupportedAspectVersionError(
                f"{self.path}: ASPECT major version 3 is required; "
                f"found {self.version}"
            )

    def _parse_timestep(self, line: str, line_number: int) -> AspectTimestep:
        match = _TIMESTEP_PATTERN.fullmatch(line)
        if match is None:
            raise self._parse_error(line_number, "malformed timestep header")

        time_unit = match.group("time_unit")
        timestep_unit = match.group("timestep_unit")
        if time_unit != timestep_unit:
            raise self._parse_error(
                line_number,
                "time and timestep units differ "
                f"({time_unit!r} != {timestep_unit!r})",
            )

        return AspectTimestep(
            number=int(match.group("number")),
            time=float(match.group("time")),
            timestep_size=float(match.group("timestep_size")),
            time_unit=time_unit,
            line_number=line_number,
        )

    def _parse_timing_section(
        self, line: str, line_number: int
    ) -> AspectTimingSection:
        columns = [column.strip() for column in line.split("|")]
        if len(columns) != 6 or columns[0] or columns[-1]:
            raise self._parse_error(line_number, "malformed timing row")

        name, call_count, wall_time, percent = columns[1:-1]
        wall_time_match = _SECONDS_PATTERN.fullmatch(wall_time)
        percent_match = _PERCENT_PATTERN.fullmatch(percent)
        if (
            not name
            or not call_count.isdigit()
            or wall_time_match is None
            or percent_match is None
        ):
            raise self._parse_error(line_number, "malformed timing row")

        return AspectTimingSection(
            name=name,
            call_count=int(call_count),
            wall_time_seconds=float(wall_time_match.group("value")),
            percent_of_total=float(percent_match.group("value")),
        )

    @staticmethod
    def _is_table_separator(line: str) -> bool:
        return line.lstrip().startswith("+")

    def _parse_error(self, line_number: int, message: str) -> ValueError:
        return ValueError(f"{self.path}:{line_number}: {message}")
