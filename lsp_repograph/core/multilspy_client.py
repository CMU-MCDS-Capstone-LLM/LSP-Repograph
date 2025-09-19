"""
Jedi LSP client using multilspy for semantic code analysis
Provides three core APIs: search symbol, find definition, find references
"""

from pathlib import Path
from typing import Dict, List, Any
import tempfile
import os
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger


class MultilspyLSPClient:
    """
    LSP client using multilspy with Jedi language server
    Provides three core APIs without result formatting
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.server = None
        self._initialize_multilspy()
    
    def _initialize_multilspy(self):
        """Initialize multilspy with Jedi configuration"""
        try:
            config = MultilspyConfig.from_dict({
                "code_language": "python",
                "trace_lsp_communication": False
            })
            logger = MultilspyLogger()
            
            self.server = SyncLanguageServer.create(config, logger, str(self.repo_path))
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize multilspy: {e}")
    
    def search_symbol(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols across entire workspace
        
        Args:
            query: Symbol name to search for
            
        Returns:
            Raw multilspy workspace symbol results
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_workspace_symbol(query)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error in symbol search: {e}")
            return []
        
    def find_definition(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """
        Find definition at specific position
        
        Args:
            file_path: Absolute path to file
            line: 0-indexed line number
            character: 0-indexed character position
            
        Returns:
            Raw multilspy definition results
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_definition(file_path, line, character)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error finding definition: {e}")
            return []
    
    def find_references(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """
        Find all references to symbol at position
        
        Args:
            file_path: Absolute path to file
            line: 0-indexed line number  
            character: 0-indexed character position
            
        Returns:
            Raw multilspy reference results
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_references(file_path, line, character)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error finding references: {e}")
            return []
    
    def find_methods(self, file_path: str, line: int, character: int) -> List[Dict[str, any]]:
        """
        Find all methods of a class defined at position. 
        
        Args:
            file_path: Absolute path to file
            line: 0-indexed line number  
            character: 0-indexed character position
            
        Returns:
            All methods of the class, or empty list of symbol is not class

        Note:
            This method is powered by AST analysis of the class source code
        """
        # TODO: Implement this
        # TODO: Combine find_methods and find_references into find_neighbors method
        raise NotImplementedError("Not implemented yet.")
    
    def shutdown(self):
        """
        Cleanly shutdown the server
        Note: multilspy handles server lifecycle in context manager
        """
        self.server = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.shutdown()