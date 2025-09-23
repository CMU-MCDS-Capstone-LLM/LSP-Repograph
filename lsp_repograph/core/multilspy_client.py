"""
Jedi LSP client using multilspy for semantic code analysis
Provides three core APIs: search symbol, find definition, find references
"""

from pathlib import Path
from typing import Dict, List, Any
import tempfile
import os
import uuid
from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

from lsp_repograph.core.lsp.jedi_language_server.custom_jedi_server import CustomJediServer

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
            
            # self.server = SyncLanguageServer.create(config, logger, str(self.repo_path))
            self.server = SyncLanguageServer(CustomJediServer(config, logger, str(self.repo_path)), timeout=None)
            
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
            Filtered multilspy reference results (excludes venv directories)
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_references(file_path, line, character)
                if not isinstance(result, list):
                    return []
                
                # Filter out references from venv directories
                filtered_result = []
                for ref in result:
                    # Check if reference is in venv directory
                    if self._is_in_venv(ref):
                        continue
                    filtered_result.append(ref)
                
                return filtered_result
        except Exception as e:
            print(f"Error finding references: {e}")
            return []
    
    def _is_in_venv(self, reference: Dict[str, Any]) -> bool:
        """
        Check if a reference is in a virtual environment directory
        
        Args:
            reference: Reference result from multilspy
            
        Returns:
            True if reference is in venv, False otherwise
        """
        # Check both absolutePath and relativePath fields
        paths_to_check = []
        
        if 'absolutePath' in reference:
            paths_to_check.append(reference['absolutePath'])
        if 'relativePath' in reference:
            paths_to_check.append(reference['relativePath'])
        if 'uri' in reference:
            # Extract path from URI
            uri = reference['uri']
            if uri.startswith('file://'):
                paths_to_check.append(uri[7:])  # Remove 'file://' prefix
        
        # Common venv directory patterns
        venv_patterns = [
            '/venv/', '\\venv\\',
            '/env/', '\\env\\', 
            '/.venv/', '\\.venv\\',
            '/site-packages/', '\\site-packages\\',
            '/lib/python', '\\lib\\python',
            '/Scripts/', '\\Scripts\\',
            '/bin/python', '\\bin\\python'
        ]
        
        for path in paths_to_check:
            if path:
                path_str = str(path).lower()
                for pattern in venv_patterns:
                    if pattern in path_str:
                        return True
        
        return False
    
    def search_ws_symbol_def(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for workspace symbol definitions
        
        Args:
            query: Symbol name to search for (supports path-like queries)
            
        Returns:
            List of workspace symbol definitions
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                result = self.server.request_workspace_symbol(query)
                return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Error searching workspace symbols: {e}")
            return []
    
    def search_non_ws_symbol_def(self, library: str, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Search for non-workspace symbol definitions using scratch file approach
        
        Args:
            library: Library name (e.g., "os.path", "numpy", "builtins")
            symbol: Symbol name within library (optional)
            
        Returns:
            List of symbol definitions
        """
        if not self.server:
            return []
        # Create scratch file content
        if symbol is None:
            # Search for library definition
            scratch_content = f"import {library}"
            target_line = 0
            target_char = 7  # Position after "import "
        else:
            # Search for specific symbol in library
            scratch_content = f"import {library} as __m\n__m.{symbol}"
            target_line = 1
            target_char = len(f"__m.{symbol}") - 1
        
        # Create temporary scratch file
        scratch_filename = f"_scratch_{uuid.uuid4().hex[:8]}.py"
        scratch_path = self.repo_path / scratch_filename
        
        try:
            # Write scratch file
            with open(scratch_path, 'w') as f:
                f.write(scratch_content)
            
            with self.server.start_server():
                # Get definition at the target position
                definitions = self.server.request_definition(str(scratch_path), target_line, target_char)
                
                # # TODO: Enhance results with symbol type information
                # enhanced_results = []
                # for definition in definitions if isinstance(definitions, list) else []:
                #     # Get document symbols to determine symbol type
                #     if 'relativePath' in definition:
                #         # This will return type of all symbols, which can be costly
                #         doc_symbols = self.server.request_document_symbols(definition['relativePath'])
                #         # Find matching symbol by location
                #         symbol_type = self._find_symbol_type_at_location(doc_symbols, definition)
                #         definition['symbolType'] = symbol_type
                    
                #     enhanced_results.append(definition)
                
                # return enhanced_results
                return definitions
                
        except Exception as e:
            print(f"Error searching non-workspace symbols: {e}")
            return []
        finally:
            # Clean up scratch file
            if scratch_path.exists():
                scratch_path.unlink()
    
    def search_non_workspace_library_symbol(self, library: str, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Search for symbol definitions in standard library or third-party library
        
        Args:
            library: Library name (e.g., "os.path", "numpy")
            symbol: Symbol name within library (optional)
            
        Returns:
            List of symbol definitions
        """
        return self.search_non_ws_symbol_def(library, symbol)
    
    def search_builtins_symbol_def(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Search for builtin symbol definitions
        
        Args:
            symbol: Symbol name (optional)
            
        Returns:
            List of builtin symbol definitions
        """
        return self.search_non_ws_symbol_def("builtins", symbol)
    
    def find_non_ws_symbol_refs(self, library: str, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Find references to non-workspace symbols using scratch file approach
        
        Args:
            library: Library name (e.g., "os.path", "numpy", "builtins") 
            symbol: Symbol name within library (optional)
            
        Returns:
            List of reference locations (filtered to exclude venv and scratch file itself)
        """
        if not self.server:
            return []
        
        # Create scratch file content
        if symbol is None:
            # Search for library references
            scratch_content = f"import {library}"
            target_line = 0
            target_char = 7  # Position after "import "
        else:
            # Search for specific symbol references in library
            scratch_content = f"import {library} as __m\n__m.{symbol}"
            target_line = 1
            target_char = len(f"__m.{symbol}") - 1
        
        # Create temporary scratch file
        scratch_filename = f"_scratch_{uuid.uuid4().hex[:8]}.py"
        scratch_path = self.repo_path / scratch_filename
        
        try:
            # Write scratch file
            with open(scratch_path, 'w') as f:
                f.write(scratch_content)
            
            with self.server.start_server():
                # Get references at the target position
                references = self.server.request_references(str(scratch_path), target_line, target_char)
                
                if not isinstance(references, list):
                    return []
                
                # Filter out references from venv and scratch file itself
                filtered_refs = []
                for ref in references:
                    # Skip references in venv directories
                    if self._is_in_venv(ref):
                        continue
                    
                    # Skip references from the scratch file itself
                    if self._is_scratch_file_ref(ref, scratch_path):
                        continue
                    
                    filtered_refs.append(ref)
                
                return filtered_refs
                
        except Exception as e:
            print(f"Error finding non-workspace symbol references: {e}")
            return []
        finally:
            # Clean up scratch file
            if scratch_path.exists():
                scratch_path.unlink()
    
    def find_non_workspace_library_symbol_refs(self, library: str, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Find references to standard library or third-party library symbols
        
        Args:
            library: Library name (e.g., "os.path", "numpy")
            symbol: Symbol name within library (optional)
            
        Returns:
            List of reference locations
        """
        return self.find_non_ws_symbol_refs(library, symbol)
    
    def find_builtins_symbol_refs(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        Find references to builtin symbols
        
        Args:
            symbol: Symbol name (optional, defaults to builtins module)
            
        Returns:
            List of reference locations  
        """
        return self.find_non_ws_symbol_refs("builtins", symbol)
    
    def find_ws_symbol_refs(self, query: str) -> List[Dict[str, Any]]:
        """
        Find references to workspace symbol by full path query
        
        Args:
            query: Full path to symbol (e.g., "core.math_utils.Calculator.add")
            
        Returns:
            List of reference locations, or empty list if symbol is ambiguous or not found
        """
        if not self.server:
            return []
            
        try:
            with self.server.start_server():
                # First, search for the symbol definition
                symbol_defs = self.server.request_workspace_symbol(query)
                
                if not isinstance(symbol_defs, list):
                    print(f"No workspace symbols found for query: '{query}'")
                    return []
                
                if len(symbol_defs) == 0:
                    print(f"No workspace symbols found for query: '{query}'")
                    return []
                
                if len(symbol_defs) > 1:
                    print(f"Ambiguous query '{query}' - found {len(symbol_defs)} symbols:")
                    for i, symbol in enumerate(symbol_defs):
                        location = symbol.get('location', {})
                        uri = location.get('uri', 'unknown')
                        range_info = location.get('range', {})
                        start = range_info.get('start', {})
                        line = start.get('line', 0)
                        print(f"  {i+1}. {symbol.get('name', 'unknown')} at {uri}:{line+1}")
                    print("Please use a more specific query or use find-def-at-pos with exact location")
                    return []
                
                # Exactly one symbol found - get its location and find references
                symbol = symbol_defs[0]
                location = symbol['location']
                
                # Extract file path from URI
                uri = location['uri']
                if uri.startswith('file://'):
                    file_path = uri[7:]  # Remove 'file://' prefix
                else:
                    file_path = uri
                
                # Extract position
                range_info = location['range']
                line = range_info['start']['line']
                character = range_info['start']['character']
                
                print(f"Found unique symbol '{symbol.get('name', 'unknown')}' at {file_path}:{line+1}:{character}")
                print("Finding references...")
                
                # Find references at this location
                references = self.server.request_references(file_path, line, character)
                
                if not isinstance(references, list):
                    return []
                
                # Filter out venv references
                filtered_refs = []
                for ref in references:
                    if not self._is_in_venv(ref):
                        filtered_refs.append(ref)
                
                return filtered_refs
                
        except Exception as e:
            print(f"Error finding workspace symbol references: {e}")
            return []
    
    def _is_scratch_file_ref(self, reference: Dict[str, Any], scratch_path: Path) -> bool:
        """
        Check if a reference is from the scratch file itself
        
        Args:
            reference: Reference result from multilspy
            scratch_path: Path to the scratch file
            
        Returns:
            True if reference is from scratch file, False otherwise
        """
        scratch_path_str = str(scratch_path)
        
        # Check absolutePath field
        if 'absolutePath' in reference:
            if reference['absolutePath'] == scratch_path_str:
                return True
        
        # Check relativePath field
        if 'relativePath' in reference:
            # Convert to absolute path for comparison
            relative_abs = str(self.repo_path / reference['relativePath'])
            if relative_abs == scratch_path_str:
                return True
        
        # Check URI field
        if 'uri' in reference:
            uri = reference['uri']
            if uri.startswith('file://'):
                uri_path = uri[7:]  # Remove 'file://' prefix
                if uri_path == scratch_path_str:
                    return True
        
        return False
    
    def _find_symbol_type_at_location(self, doc_symbols: List[Dict], target_definition: Dict) -> str:
        """
        Find symbol type by matching location in document symbols
        
        Args:
            doc_symbols: Document symbols from LSP
            target_definition: Definition location to match
            
        Returns:
            Symbol type string or "Unknown"
        """
        if not doc_symbols or 'range' not in target_definition:
            return "Unknown"
        
        target_range = target_definition['range']
        target_line = target_range['start']['line']
        target_char = target_range['start']['character']
        
        def search_symbols(symbols):
            for symbol in symbols:
                if 'range' in symbol:
                    symbol_range = symbol['range']
                    symbol_line = symbol_range['start']['line']
                    symbol_char = symbol_range['start']['character']
                    
                    # Check if this symbol matches the target location
                    if symbol_line == target_line and symbol_char == target_char:
                        return self._format_symbol_kind(symbol.get('kind', 1))
                    
                    # Check nested symbols (children)
                    if 'children' in symbol:
                        result = search_symbols(symbol['children'])
                        if result != "Unknown":
                            return result
            return "Unknown"
        
        return search_symbols(doc_symbols)
    
    def _format_symbol_kind(self, kind: int) -> str:
        """Convert LSP symbol kind number to string"""
        kinds = {
            1: "File", 2: "Module", 3: "Namespace", 4: "Package", 5: "Class",
            6: "Method", 7: "Property", 8: "Field", 9: "Constructor", 10: "Enum",
            11: "Interface", 12: "Function", 13: "Variable", 14: "Constant",
            15: "String", 16: "Number", 17: "Boolean", 18: "Array", 19: "Object",
            20: "Key", 21: "Null", 22: "EnumMember", 23: "Struct", 24: "Event",
            25: "Operator", 26: "TypeParameter"
        }
        return kinds.get(kind, "Unknown")
    
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
