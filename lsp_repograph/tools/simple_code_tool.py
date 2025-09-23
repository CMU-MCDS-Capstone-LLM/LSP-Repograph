"""
Simple code search tool for AI agents
LSP-first approach using Pyright for semantic analysis
"""

from pathlib import Path
from typing import List, Dict, Any
from ..core.multilspy_client import MultilspyLSPClient
from ..core.multilspy_result_formatter import MultilspyResultFormatter

class SimpleCodeTool:
    """
    LSP-first code search tool - leverages Pyright's built-in indexing
    No text scanning - pure LSP approach for maximum performance
    """
    
    def __init__(self, repo_path: str, custom_init_params: dict = None):
        """
        Initialize tool with repository path and optional custom initialization parameters
        
        Args:
            repo_path: Path to repository to analyze
            custom_init_params: Custom initialization parameters to override defaults.
                               Example: {
                                   "initializationOptions": {
                                       "workspace": {
                                           "extraPaths": ["/path/to/venv/site-packages"],
                                           "environmentPath": "/path/to/venv/bin/python"
                                       }
                                   }
                               }
        """
        self.repo_path = Path(repo_path).resolve()
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
            
        print("Starting Jedi LSP server (Multilspy - Jedi Langauge Server)...")
        self.lsp_client = MultilspyLSPClient(str(self.repo_path), custom_init_params)
        self.formatter = MultilspyResultFormatter(str(self.repo_path))
        print("LSP server ready")
    
    def where_defined(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Find where a symbol is defined using LSP workspace symbols
        
        Args:
            symbol_name: Name of function/class/variable to find definitions for
            
        Returns:
            List of definition locations with file, line, context
        """
        # Use LSP workspace symbol search - much faster than text scanning
        workspace_symbols = self.lsp_client.workspace_symbol_search(symbol_name)
        
        definitions = []
        for symbol in workspace_symbols:
            # Filter to exact matches (workspace search can be fuzzy)
            if symbol.get('name') == symbol_name:
                formatted = self.formatter.format_workspace_symbol(symbol, 'definition')
                if formatted:
                    definitions.append(formatted)
        
        return self._deduplicate_results(definitions)
    
    def where_used(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Find where a symbol is used using LSP references
        
        Args:
            symbol_name: Name of function/class/variable to find usages for
            
        Returns:
            List of reference locations with file, line, context
        """
        # Step 1: Find definitions using workspace symbols
        definitions = self.where_defined(symbol_name)
        
        if not definitions:
            return []
        
        # Step 2: For each definition, get all references via LSP
        all_references = []
        
        for defn in definitions:
            # Convert relative path back to absolute
            file_path = self.repo_path / defn['file']
            line_num = defn['line'] - 1  # Convert to 0-indexed for LSP
            
            # Get references from LSP
            lsp_references = self.lsp_client.get_references(
                str(file_path),
                line_num,
                defn['column'],
                include_declaration=True  # Include the definition itself
            )
            
            # Format results
            if lsp_references:
                formatted_refs = self.formatter.format_references(lsp_references)
                all_references.extend(formatted_refs)
        
        return self._deduplicate_results(all_references)
    
    def search_symbol(self, symbol_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get both definitions and references for a symbol
        
        Args:
            symbol_name: Symbol to search for
            
        Returns:
            Dict with 'definitions' and 'references' keys
        """
        definitions = self.where_defined(symbol_name)
        references = self.where_used(symbol_name)
        
        # Separate definitions from references in the results
        pure_references = [
            ref for ref in references 
            if ref['type'] == 'reference'
        ]
        
        return {
            'definitions': definitions,
            'references': pure_references
        }
    
    def explore_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all symbols defined in a specific file
        Useful for exploration and understanding file structure
        
        Args:
            file_path: Relative path to file from repo root
            
        Returns:
            List of symbols defined in the file
        """
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return []
        
        symbols = self.lsp_client.get_document_symbols(str(full_path))
        return self.formatter.format_document_symbols(symbols, file_path)
    
    def find_symbol_at_position(self, file_path: str, line: int, column: int) -> Dict[str, Any]:
        """
        Get information about symbol at specific position
        
        Args:
            file_path: Relative path to file from repo root
            line: 1-indexed line number
            column: 0-indexed column number
            
        Returns:
            Dict with definition and reference information
        """
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return {'definitions': [], 'references': []}
        
        # Convert to 0-indexed for LSP
        lsp_line = line - 1
        
        # Get definition
        definitions = self.lsp_client.get_definition(str(full_path), lsp_line, column)
        formatted_defs = self.formatter.format_definitions(definitions) if definitions else []
        
        # Get references
        references = self.lsp_client.get_references(str(full_path), lsp_line, column)
        formatted_refs = self.formatter.format_references(references) if references else []
        
        return {
            'definitions': formatted_defs,
            'references': formatted_refs
        }
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on file, line, and column"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result['file'], result['line'], result['column'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
                
        return unique_results
    
    def shutdown(self):
        """Shutdown the LSP server"""
        if hasattr(self, 'lsp_client'):
            self.lsp_client.shutdown()
    
    def __del__(self):
        """Cleanup LSP server process on destruction"""
        self.shutdown()
