"""Parser for ASPECT statistics files."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

_COLUMN_PATTERN = re.compile(r"^\s*#\s*(?P<number>\d+):\s*(?P<name>.*?)\s*$")
_NAME_AND_UNIT_PATTERN = re.compile(
    r"^(?P<name>.*?)(?:\s+\((?P<unit>[^()]*)\))?$"
)


class AspectStatistics:
    """Read a column-oriented ASPECT statistics file.

    ASPECT records the meaning of each column in numbered comment lines at the
    beginning of the file. The available columns depend on the enabled
    postprocessors, so this class preserves their original names and order
    instead of imposing a fixed schema.

    Parameters
    ----------
    path
        Path to an ASPECT ``statistics`` file.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)
        self._data, self._units = self._parse()

    @property
    def data(self) -> pd.DataFrame:
        """Return the parsed statistics table as a pandas DataFrame."""
        return self._data

    @property
    def units(self) -> Dict[str, Optional[str]]:
        """Return the unit for each DataFrame column, or ``None`` if absent."""
        return self._units.copy()

    def _parse(self) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
        column_names: List[str] = []
        units: Dict[str, Optional[str]] = {}
        rows: List[List[str]] = []
        data_started = False

        with self.path.open(encoding="utf-8", errors="replace") as stream:
            for line_number, line in enumerate(stream, start=1):
                stripped = line.strip()
                if not stripped:
                    continue

                column_match = _COLUMN_PATTERN.fullmatch(line.rstrip("\r\n"))
                if column_match is not None:
                    if data_started:
                        raise self._parse_error(
                            line_number, "column definition follows data rows"
                        )

                    number = int(column_match.group("number"))
                    expected_number = len(column_names) + 1
                    if number != expected_number:
                        raise self._parse_error(
                            line_number,
                            f"expected column {expected_number}, found column {number}",
                        )

                    name_and_unit_match = _NAME_AND_UNIT_PATTERN.fullmatch(
                        column_match.group("name")
                    )
                    assert name_and_unit_match is not None
                    name = name_and_unit_match.group("name")
                    unit = name_and_unit_match.group("unit") or None
                    if not name:
                        raise self._parse_error(line_number, "empty column name")
                    if name in column_names:
                        raise self._parse_error(
                            line_number, f"duplicate column name {name!r}"
                        )
                    column_names.append(name)
                    units[name] = unit
                    continue

                if stripped.startswith("#"):
                    continue
                if not column_names:
                    raise self._parse_error(
                        line_number, "data row precedes column definitions"
                    )

                data_started = True
                try:
                    values = shlex.split(line, comments=False, posix=True)
                except ValueError as error:
                    raise self._parse_error(
                        line_number, f"malformed quoted value: {error}"
                    ) from error

                if len(values) != len(column_names):
                    raise self._parse_error(
                        line_number,
                        f"expected {len(column_names)} values, found {len(values)}",
                    )
                rows.append(values)

        if not column_names:
            raise ValueError(f"{self.path}: no statistics columns found")

        data = pd.DataFrame(rows, columns=column_names)
        for name in column_names:
            try:
                data[name] = pd.to_numeric(data[name], errors="raise")
            except (TypeError, ValueError):
                pass
        return data, units

    def _parse_error(self, line_number: int, message: str) -> ValueError:
        return ValueError(f"{self.path}:{line_number}: {message}")
