from __future__ import annotations

from typing import Dict, Iterable, Tuple


def parse_flag_args(args: Iterable[str]) -> Dict[str, str]:
    """Parse `--key value` pairs from the REPL command arguments."""
    result: Dict[str, str] = {}
    iterator = iter(args)

    for token in iterator:
        if not token.startswith("--"):
            raise ValueError(f"Unexpected token '{token}'. Flags must start with '--'.")

        key = token[2:]
        try:
            value = next(iterator)
        except StopIteration as exc:  # pragma: no cover - validated via REPL usage
            raise ValueError(f"Missing value for flag '--{key}'") from exc

        result[key] = value

    return result


def parse_bool(value: str | None, *, default: bool) -> bool:
    """Convert common string representations of booleans to bool."""
    if value is None:
        return default

    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def read_file_line(file_path: str, line_number: int) -> str:
    """Read a specific line from a file (0-indexed)."""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except Exception as exc:  # pragma: no cover - IO errors surface to user directly
        return f"<Error reading file: {exc}>"

    if 0 <= line_number < len(lines):
        return lines[line_number].rstrip("\n")
    return "<Line not found>"


def format_location_for_display(path: str, line: int, character: int) -> Tuple[str, str]:
    """Produce display strings for definition/reference printing."""
    header = f"File \"{path}\", line {line}, character {character}"
    content = read_file_line(path, line)
    return header, content
