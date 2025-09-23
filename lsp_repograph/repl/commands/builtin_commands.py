from typing import List
from pprint import pprint
from .base import Command
from .utils import format_reference_with_content
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class FindBuiltinDefinitionCommand(Command):
    """Find builtin symbol definitions"""
    
    @property
    def name(self) -> str:
        return "find-builtin-def"
    
    @property
    def description(self) -> str:
        return "Find builtin symbol definitions"
    
    @property
    def usage(self) -> str:
        return "find-builtin-def [symbol]"
    
    @property
    def example(self) -> str:
        return "find-builtin-def int"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        symbol = args[0] if len(args) > 0 else None
        
        if symbol:
            print(f"Searching for builtin symbol '{symbol}'")
        else:
            print("Searching for builtins module definition")
        
        result = client.search_builtins_symbol_def(symbol)
        print(f"\nFound {len(result)} builtin symbols:")
        pprint(result)


class FindBuiltinReferencesCommand(Command):
    """Find builtin symbol references"""
    
    @property
    def name(self) -> str:
        return "find-builtin-refs"
    
    @property
    def description(self) -> str:
        return "Find builtin symbol references"
    
    @property
    def usage(self) -> str:
        return "find-builtin-refs [symbol]"
    
    @property
    def example(self) -> str:
        return "find-builtin-refs print"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        symbol = args[0] if len(args) > 0 else None
        
        if symbol:
            print(f"Searching for references to builtin symbol '{symbol}'")
        else:
            print("Searching for references to builtins module")
        
        result = client.find_builtins_symbol_refs(symbol)
        print(f"\nFound {len(result)} builtin symbol references:")
        if result:
            for ref in result:
                print(format_reference_with_content(ref))
        else:
            print("No references found.")