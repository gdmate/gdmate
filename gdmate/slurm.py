"""Parse and make localized edits to SLURM batch-file headers."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

PathLike = Union[str, Path]

__all__ = ["SlurmScript"]

_DIRECTIVE_RE = re.compile(
    r"^(?P<prefix>[ \t]*#[ \t]*SBATCH[ \t]+)"
    r"(?P<option>--?[^\s=]+)"
    r"(?:(?P<separator>=|[ \t]+)(?P<value>.*?))?"
    r"(?P<comment>[ \t]+#.*)?"
    r"(?P<newline>\r?\n)?$"
)


@dataclass(frozen=True)
class _SlurmDirective:
    """A parsed ``#SBATCH`` option and its value."""

    option: str
    value: str
    line_number: int


class SlurmScript:
    """A SLURM script whose header can be edited without rewriting its body."""

    def __init__(self, text: str):
        self._lines = text.splitlines(keepends=True)
        if text and not self._lines:
            self._lines = [text]
        self._refresh()

    @classmethod
    def from_file(cls, path: PathLike) -> "SlurmScript":
        """Read a SLURM script without newline conversion."""
        with Path(path).open("r", encoding="utf-8", newline="") as stream:
            return cls(stream.read())

    def _refresh(self) -> None:
        parsed = []
        last_directive = None
        for index, line in enumerate(self._lines):
            match = _DIRECTIVE_RE.match(line)
            if match is None:
                continue
            parsed.append(
                _SlurmDirective(
                    option=match.group("option"),
                    value=match.group("value") or "",
                    line_number=index + 1,
                )
            )
            last_directive = index

        if last_directive is None:
            raise ValueError("SLURM script does not contain an SBATCH directive")

        header_end = last_directive + 1
        while header_end < len(self._lines) and not self._lines[header_end].strip():
            header_end += 1

        self._directives = parsed
        self._header_end = header_end

    @property
    def directives(self) -> List[_SlurmDirective]:
        """Return read-only directive records in their original order."""
        return list(self._directives)

    @property
    def header(self) -> str:
        """Return the header, including the separator before the body."""
        return "".join(self._lines[: self._header_end])

    @property
    def body(self) -> str:
        """Return the executable portion of the script exactly as parsed."""
        return "".join(self._lines[self._header_end :])

    @property
    def text(self) -> str:
        """Return the complete current script."""
        return "".join(self._lines)

    def get_directive(self, option: str) -> str:
        """Return the value of the last matching directive."""
        for directive in reversed(self._directives):
            if directive.option == option:
                return directive.value
        raise KeyError(option)

    def set_directive(self, option: str, value: str) -> None:
        """Replace a directive value while retaining its syntax and comment."""
        matches = [item for item in self._directives if item.option == option]
        if not matches:
            raise KeyError(option)

        directive = matches[-1]
        index = directive.line_number - 1
        line = self._lines[index]
        match = _DIRECTIVE_RE.match(line)
        if match is None or match.group("separator") is None:
            raise ValueError(f"SBATCH directive {option!r} does not accept a value")

        start, end = match.span("value")
        self._lines[index] = f"{line[:start]}{value}{line[end:]}"
        self._refresh()

    def write(self, path: PathLike) -> None:
        """Write the current script without newline conversion."""
        with Path(path).open("w", encoding="utf-8", newline="") as stream:
            stream.write(self.text)
