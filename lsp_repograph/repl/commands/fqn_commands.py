from __future__ import annotations

from typing import List

from .base import Command
from .utils import format_location_for_display, parse_bool, parse_flag_args
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class FindDefByFqnCommand(Command):
    """Find definition using a module + qualpath FQN."""

    @property
    def name(self) -> str:  # pragma: no cover - trivial property
        return "find-def-by-fqn"

    @property
    def description(self) -> str:  # pragma: no cover
        return "Find the definition location for <module>:<qualpath> (hover optional)."

    @property
    def usage(self) -> str:  # pragma: no cover
        return "find-def-by-fqn --module <module> [--qualpath <qualpath>] [--with_hover_msg <bool>]"

    @property
    def example(self) -> str:  # pragma: no cover
        return "find-def-by-fqn --module collections --qualpath deque.popleft"

    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        try:
            flags = parse_flag_args(args)
        except ValueError as exc:
            print(f"Error: {exc}")
            print(f"Usage: {self.usage}")
            return

        module = flags.get("module")
        qualpath = flags.get("qualpath")
        try:
            with_hover = parse_bool(flags.get("with_hover_msg"), default=True)
        except ValueError as exc:
            print(f"Error: {exc}")
            print(f"Usage: {self.usage}")
            return

        if not module:
            print("Error: --module flag is required")
            print(f"Usage: {self.usage}")
            return

        symbol_display = f"{module}:{qualpath}" if qualpath else module

        try:
            result = client.find_def_by_fqn(module=module, qualpath=qualpath, with_hover_msg=with_hover)
        except Exception as exc:  # pragma: no cover - surfaces runtime issues to user
            print(f"No definition found for {symbol_display}")
            return

        if not result:
            print(f"No definition found for {symbol_display}")
            return

        path = result["absolute_path"]
        line = result["line"]
        character = result["character"]

        print(f"Found definition of {symbol_display} in file \"{path}\", line {line}, character {character}")
        _, content = format_location_for_display(path, line, character)
        print(content)

        hover_text = result.get("hover_text")
        if with_hover and hover_text:
            print("\nHover Text:")
            print(hover_text)


class FindRefsByFqnCommand(Command):
    """Find references using a module + qualpath FQN."""

    @property
    def name(self) -> str:  # pragma: no cover
        return "find-refs-by-fqn"

    @property
    def description(self) -> str:  # pragma: no cover
        return "List all references for <module>:<qualpath>."

    @property
    def usage(self) -> str:  # pragma: no cover
        return "find-refs-by-fqn --module <module> [--qualpath <qualpath>]"

    @property
    def example(self) -> str:  # pragma: no cover
        return "find-refs-by-fqn --module pathlib --qualpath Path.read_text"

    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        try:
            flags = parse_flag_args(args)
        except ValueError as exc:
            print(f"Error: {exc}")
            print(f"Usage: {self.usage}")
            return

        module = flags.get("module")
        qualpath = flags.get("qualpath")

        if not module:
            print("Error: --module flag is required")
            print(f"Usage: {self.usage}")
            return

        symbol_display = f"{module}:{qualpath}" if qualpath else module

        try:
            references = client.find_refs_by_fqn(module=module, qualpath=qualpath)
        except Exception as exc:  # pragma: no cover
            print(f"Error executing reference lookup: {exc}")
            return

        print(f"Found {len(references)} references of {symbol_display} at these locations")

        if not references:
            return

        for ref in references:
            path = ref["absolute_path"]
            line = ref["line"]
            character = ref["character"]
            header, content = format_location_for_display(path, line, character)
            print(f"\n{header}")
            print(content)
