"""Read and write deal.II/ASPECT parameter files."""

from __future__ import annotations

import re
from collections.abc import Mapping
from os import PathLike
from typing import TextIO


def parse_parameters_to_dict(file_input: TextIO) -> dict[str, str | dict]:
    """Parse a deal.II/ASPECT parameter stream into a nested dictionary.

    Comments and blank lines are ignored. Repeated subsections are merged, and
    parameter values ending in a backslash continue on the following line.
    """
    parameters: dict[str, str | dict] = {}

    while current_line := file_input.readline():
        stripped_line = current_line.lstrip()

        if not stripped_line or stripped_line.startswith("#"):
            continue

        if stripped_line.startswith("set "):
            assignment = stripped_line.removeprefix("set ")
            if "=" not in assignment:
                raise ValueError(f"Invalid parameter line: {current_line.rstrip()}")

            key, value = assignment.split("=", maxsplit=1)
            key = key.rstrip()
            value = _strip_comment_and_newline(value).lstrip()

            while value.endswith("\\"):
                continuation = file_input.readline()
                if continuation == "":
                    break
                value += "\n" + _strip_comment_and_newline(continuation)

            if value:
                parameters[key] = value
            continue

        if stripped_line.startswith("subsection "):
            subsection_name = _strip_comment_and_newline(
                stripped_line.removeprefix("subsection ")
            ).rstrip()
            subsection = parse_parameters_to_dict(file_input)
            existing = parameters.setdefault(subsection_name, {})
            if not isinstance(existing, dict):
                raise ValueError(
                    f"Subsection {subsection_name!r} conflicts with a parameter"
                )
            existing.update(subsection)
            continue

        if stripped_line.startswith("end"):
            return parameters

    return parameters


def save_parameters_from_dict(
    file_output: TextIO,
    parameters: Mapping[str, str | Mapping],
    indent_level: int = 0,
    indent_width: int = 4,
    include_path: str | PathLike[str] | None = None,
) -> None:
    """Write a nested parameter mapping in deal.II/ASPECT syntax.

    ``indent_width`` controls the number of spaces added for each nested
    subsection level. If ``include_path`` is provided, an ASPECT ``include``
    directive is written before the top-level parameters so that values in
    ``parameters`` can override values from the included file.
    """
    if include_path is not None:
        include_text = str(include_path)
        if "\n" in include_text or "\r" in include_text:
            raise ValueError("include_path must not contain a newline")
        file_output.write(f"include {include_text}\n")

    indent = " " * indent_width * indent_level

    for key, value in parameters.items():
        if isinstance(value, str):
            file_output.write(f"{indent}set {key} = {value}\n")
        elif isinstance(value, Mapping):
            if indent_level == 0:
                file_output.write("\n")

            file_output.write(f"{indent}subsection {key}\n")
            save_parameters_from_dict(
                file_output,
                value,
                indent_level + 1,
                indent_width=indent_width,
            )
            file_output.write(f"{indent}end\n")
        else:
            raise ValueError(
                "Value in parameter dictionary must be str or dict, received:"
                f"\n key: {key}\n type: {type(value)}\n value: {value}"
            )


def _strip_comment_and_newline(line: str) -> str:
    """Remove a trailing comment and line ending from a parameter line."""
    return re.sub(r"\s*(#.*)?\r?\n$", "", line)
