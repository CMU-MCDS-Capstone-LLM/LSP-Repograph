from typing import List
from pprint import pprint
from .base import Command
from .utils import format_reference_with_content
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class FindWorkspaceDefinitionCommand(Command):
    """Find workspace symbol definitions"""
    
    @property
    def name(self) -> str:
        return "find-ws-def"
    
    @property
    def description(self) -> str:
        return "Find workspace symbol definitions (excludes symbols from third-party / standard library, and built-ins)"
    
    @property
    def usage(self) -> str:
        return "find-ws-def <query>"
    
    @property
    def example(self) -> str:
        return "find-ws-def AdvancedCalculator"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        if len(args) < 1:
            print(f"Usage: {self.usage}")
            return
            
        query = ' '.join(args)
        print(f"Searching workspace symbols for: '{query}'")
        
        result = client.search_ws_symbol_def(query)
        print(f"\nFound {len(result)} workspace symbols:")
        pprint(result)


class FindWorkspaceReferencesCommand(Command):
    """Find workspace symbol references"""
    
    @property
    def name(self) -> str:
        return "find-ws-refs"
    
    @property
    def description(self) -> str:
        return "Find workspace symbol references (<query> must uniquely identify a symbol in workspace)"
    
    @property
    def usage(self) -> str:
        return "find-ws-refs <query>"
    
    @property
    def example(self) -> str:
        return "find-ws-refs core.math_utils.Calculator.add"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        if len(args) < 1:
            print(f"Usage: {self.usage}")
            return
            
        query = ' '.join(args)
        print(f"Searching workspace symbol references for: '{query}'")
        
        result = client.find_ws_symbol_refs(query)
        print(f"\nFound {len(result)} workspace symbol references:")
        if result:
            for ref in result:
                print(format_reference_with_content(ref))
        else:
            print("No references found.")
