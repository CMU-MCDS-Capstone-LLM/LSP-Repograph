from typing import List
from pprint import pprint
from .base import Command
from .utils import format_reference_with_content
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class FindLibraryDefinitionCommand(Command):
    """Find library symbol definitions"""
    
    @property
    def name(self) -> str:
        return "find-lib-def"
    
    @property
    def description(self) -> str:
        return "Find library symbol definitions"
    
    @property
    def usage(self) -> str:
        return "find-lib-def <library> [symbol]"
    
    @property
    def example(self) -> str:
        return "find-lib-def os.path join"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        if len(args) < 1:
            print(f"Usage: {self.usage}")
            return
            
        library = args[0]
        symbol = args[1] if len(args) > 1 else None
        
        if symbol:
            print(f"Searching for symbol '{symbol}' in library '{library}'")
        else:
            print(f"Searching for library '{library}' definition")
        
        result = client.search_non_workspace_library_symbol(library, symbol)
        print(f"\nFound {len(result)} library symbols:")
        pprint(result)


class FindLibraryReferencesCommand(Command):
    """Find library symbol references"""
    
    @property
    def name(self) -> str:
        return "find-lib-refs"
    
    @property
    def description(self) -> str:
        return "Find library symbol references"
    
    @property
    def usage(self) -> str:
        return "find-lib-refs <library> [symbol]"
    
    @property
    def example(self) -> str:
        return "find-lib-refs os.path join"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        if len(args) < 1:
            print(f"Usage: {self.usage}")
            return
            
        library = args[0]
        symbol = args[1] if len(args) > 1 else None
        
        if symbol:
            print(f"Searching for references to symbol '{symbol}' in library '{library}'")
        else:
            print(f"Searching for references to library '{library}'")
        
        result = client.find_non_workspace_library_symbol_refs(library, symbol)
        print(f"\nFound {len(result)} library symbol references:")
        if result:
            for ref in result:
                print(format_reference_with_content(ref))
        else:
            print("No references found.")