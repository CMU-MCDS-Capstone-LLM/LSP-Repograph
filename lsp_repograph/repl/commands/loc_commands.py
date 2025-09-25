from __future__ import annotations

from typing import List

from .base import Command
from .utils import format_location_for_display, parse_bool, parse_flag_args
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class FindDefByLocCommand(Command):
    """Find definition by caret location."""

    @property
    def name(self) -> str:  # pragma: no cover
        return "find-def-by-loc"

    @property
    def description(self) -> str:  # pragma: no cover
        return "Resolve definition from a repo-relative file position (hover optional)."

    @property
    def usage(self) -> str:  # pragma: no cover
        return "find-def-by-loc --rel_path <rel_path> --line <line> --character <character> [--with_hover_msg <bool>]"

    @property
    def example(self) -> str:  # pragma: no cover
        return "find-def-by-loc --rel_path app/io_utils.py --line 42 --character 25"

    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        try:
            flags = parse_flag_args(args)
        except ValueError as exc:
            print(f"Error: {exc}")
            print(f"Usage: {self.usage}")
            return

        rel_path = flags.get("rel_path")
        line_str = flags.get("line")
        char_str = flags.get("character")

        try:
            with_hover = parse_bool(flags.get("with_hover_msg"), default=True)
        except ValueError as exc:
            print(f"Error: {exc}")
            print(f"Usage: {self.usage}")
            return

        if not rel_path or line_str is None or char_str is None:
            print("Error: --rel_path, --line, and --character flags are required")
            print(f"Usage: {self.usage}")
            return

        try:
            line = int(line_str)
            character = int(char_str)
        except ValueError:
            print("Error: --line and --character must be integers")
            return

        try:
            result = client.find_def_by_loc(
                rel_path=rel_path,
                line=line,
                character=character,
                with_hover_msg=with_hover,
            )
        except Exception as exc:  # pragma: no cover
            print("No definition found for the supplied location")
            return

        if not result:
            print("No definition found for the supplied location")
            return

        path = result["absolute_path"]
        line_num = result["line"]
        char_num = result["character"]

        print(
            "Found definition at file \"{path}\", line {line}, character {char}".format(
                path=path,
                line=line_num,
                char=char_num,
            )
        )
        _, content = format_location_for_display(path, line_num, char_num)
        print(content)

        hover_text = result.get("hover_text")
        if with_hover and hover_text:
            print("\nHover Text:")
            print(hover_text)


class FindRefsByLocCommand(Command):
    """Find references by caret location."""

    @property
    def name(self) -> str:  # pragma: no cover
        return "find-refs-by-loc"

    @property
    def description(self) -> str:  # pragma: no cover
        return "List all references for the symbol at a repo-relative file position."

    @property
    def usage(self) -> str:  # pragma: no cover
        return "find-refs-by-loc --rel_path <rel_path> --line <line> --character <character>"

    @property
    def example(self) -> str:  # pragma: no cover
        return "find-refs-by-loc --rel_path app/io_utils.py --line 42 --character 25"

    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        try:
            flags = parse_flag_args(args)
        except ValueError as exc:
            print(f"Error: {exc}")
            print(f"Usage: {self.usage}")
            return

        rel_path = flags.get("rel_path")
        line_str = flags.get("line")
        char_str = flags.get("character")

        if not rel_path or line_str is None or char_str is None:
            print("Error: --rel_path, --line, and --character flags are required")
            print(f"Usage: {self.usage}")
            return

        try:
            line = int(line_str)
            character = int(char_str)
        except ValueError:
            print("Error: --line and --character must be integers")
            return

        try:
            references = client.find_refs_by_loc(rel_path=rel_path, line=line, character=character)
        except Exception as exc:  # pragma: no cover
            print(f"Error executing reference lookup: {exc}")
            return

        print(
            "Found {count} references for location {path}:{line}:{char}".format(
                count=len(references),
                path=rel_path,
                line=line,
                char=character,
            )
        )

        if not references:
            return

        for ref in references:
            path = ref["absolute_path"]
            line_num = ref["line"]
            char_num = ref["character"]
            header, content = format_location_for_display(path, line_num, char_num)
            print(f"\n{header}")
            print(content)
