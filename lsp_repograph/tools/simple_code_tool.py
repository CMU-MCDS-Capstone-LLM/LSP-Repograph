"""Simple high-level wrapper around :class:`MultilspyLSPClient`."""

from pathlib import Path
from typing import Dict, List, Optional

from ..core.multilspy_client import MultilspyLSPClient


class SimpleCodeTool:
    """Expose definition/reference helpers with minimal ceremony."""

    def __init__(self, repo_path: str, custom_init_params: Optional[dict] = None):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        print("Starting Jedi LSP server (Multilspy - Jedi Language Server)...")
        self.lsp_client = MultilspyLSPClient(str(self.repo_path), custom_init_params)
        print("LSP server ready")

    # ------------------------------------------------------------------
    # Delegated API
    # ------------------------------------------------------------------

    def find_def_by_fqn(
        self,
        module: str,
        qualpath: Optional[str] = None,
        *,
        with_hover_msg: bool = True,
    ) -> Dict[str, Optional[str]]:
        return self.lsp_client.find_def_by_fqn(module=module, qualpath=qualpath, with_hover_msg=with_hover_msg)

    def find_refs_by_fqn(self, module: str, qualpath: Optional[str] = None) -> List[Dict[str, int]]:
        return self.lsp_client.find_refs_by_fqn(module=module, qualpath=qualpath)

    def find_def_by_loc(
        self,
        rel_path: str,
        line: int,
        character: int,
        *,
        with_hover_msg: bool = True,
    ) -> Dict[str, Optional[str]]:
        return self.lsp_client.find_def_by_loc(
            rel_path=rel_path,
            line=line,
            character=character,
            with_hover_msg=with_hover_msg,
        )

    def find_refs_by_loc(self, rel_path: str, line: int, character: int) -> List[Dict[str, int]]:
        return self.lsp_client.find_refs_by_loc(rel_path=rel_path, line=line, character=character)

    def shutdown(self) -> None:
        if hasattr(self, "lsp_client"):
            self.lsp_client.shutdown()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        self.shutdown()
