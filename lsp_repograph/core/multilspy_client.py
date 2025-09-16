"""
Jedi LSP client using multilspy for semantic code analysis
Provides a unified interface similar to PyrightLSPClient but using multilspy
"""

import urllib.parse
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger


class MultilspyLSPClient:
    """
    LSP client using multilspy with Jedi language server
    Provides similar interface to PyrightLSPClient for compatibility
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
                "trace_lsp_communication": False  # Set to True for debugging
            })
            logger = MultilspyLogger()
            
            self.server = SyncLanguageServer.create(config, logger, str(self.repo_path))
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize multilspy: {e}")
    
    def workspace_symbol_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols across entire workspace using multilspy
        
        Args:
            query: Symbol name to search for
            
        Returns:
            List of symbol information with location
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_workspace_symbol(query)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error in workspace symbol search: {e}")
            return []
    
    def get_definition(self, file_path: str, line: int, character: int) -> List[Dict[str, Any]]:
        """
        Get definition at specific position
        
        Args:
            file_path: Absolute path to file
            line: 0-indexed line number
            character: 0-indexed character position
            
        Returns:
            List of location dictionaries
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_definition(file_path, line, character)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error getting definition: {e}")
            return []
    
    def get_references(self, file_path: str, line: int, character: int, 
                      include_declaration: bool = True) -> List[Dict[str, Any]]:
        """
        Get all references to symbol at position
        
        Args:
            file_path: Absolute path to file
            line: 0-indexed line number  
            character: 0-indexed character position
            include_declaration: Include the definition in results (ignored for multilspy)
            
        Returns:
            List of location dictionaries
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_references(file_path, line, character)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error getting references: {e}")
            return []
    
    def get_document_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all symbols defined in a document
        Note: This method uses multilspy's document_symbols if available
        
        Args:
            file_path: Absolute path to file
            
        Returns:
            List of document symbols
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                # Try to use document symbols if available in multilspy
                if hasattr(self.server, 'request_document_symbols'):
                    result = self.server.request_document_symbols(file_path)
                    return result if isinstance(result, list) else []
                else:
                    # Fallback: return empty list as multilspy may not support this
                    print("Document symbols not supported by multilspy")
                    return []
        except Exception as e:
            print(f"Error getting document symbols: {e}")
            return []
    
    def uri_to_path(self, uri: str) -> str:
        """
        Convert file URI to local filesystem path
        Helper method for processing multilspy results
        """
        parsed_uri = urllib.parse.urlparse(uri)
        if parsed_uri.scheme != 'file':
            raise ValueError("Provided URI is not a 'file' scheme URI.")

        path = urllib.parse.unquote(parsed_uri.path)

        # Handle Windows-specific paths starting with an extra slash
        if os.name == 'nt' and path.startswith('/'):
            # On Windows, `file:///C:/path` becomes `/C:/path` after unquoting.
            # We need to remove the leading slash for a valid Windows path.
            path = path[1:]
            # Also, convert forward slashes to backslashes for Windows
            path = path.replace('/', '\\')

        return path
    
    def shutdown(self):
        """
        Cleanly shutdown the server
        Note: multilspy handles server lifecycle in context manager
        """
        # multilspy handles shutdown automatically when exiting context manager
        self.server = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.shutdown()