"""
Result formatter for LSP responses
Converts LSP protocol responses into consistent format for AI agents
"""

from pathlib import Path
from typing import List, Dict, Any, Optional


class LSPResultFormatter:
    """Format LSP responses focusing on workspace symbols and references"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def format_workspace_symbol(self, symbol: Dict[str, Any], result_type: str) -> Optional[Dict[str, Any]]:
        """
        Format workspace symbol result
        
        Args:
            symbol: LSP workspace symbol result
            result_type: 'definition' or 'reference'
            
        Returns:
            Formatted symbol information or None if formatting fails
        """
        try:
            location = symbol['location']
            uri = location['uri']
            range_info = location['range']
            
            file_path = self._uri_to_path(uri)
            line_num = range_info['start']['line']
            
            # Get context around the symbol
            context = self._get_file_context(file_path, line_num, 2)
            
            return {
                'file': str(file_path.relative_to(self.repo_path)),
                'line': line_num + 1,  # Convert to 1-indexed for display
                'column': range_info['start']['character'],
                'context': context,
                'type': result_type,
                'symbol_kind': self._format_symbol_kind(symbol.get('kind', 1)),
                'name': symbol.get('name', ''),
                'container_name': symbol.get('containerName', '')
            }
            
        except Exception as e:
            print(f"Error formatting workspace symbol: {e}")
            return None
    
    def format_references(self, lsp_locations: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format LSP reference results
        
        Args:
            lsp_locations: List of LSP location objects
            
        Returns:
            List of formatted reference results
        """
        formatted = []
        
        for location in lsp_locations:
            try:
                uri = location['uri'] 
                range_info = location['range']
                
                file_path = self._uri_to_path(uri)
                line_num = range_info['start']['line']
                
                # Get single line context for references
                context = self._get_single_line_context(file_path, line_num)
                
                formatted.append({
                    'file': str(file_path.relative_to(self.repo_path)),
                    'line': line_num + 1,  # 1-indexed for display
                    'column': range_info['start']['character'], 
                    'context': context,
                    'type': 'reference'
                })
                
            except Exception as e:
                print(f"Error formatting reference: {e}")
                continue
                
        return formatted
    
    def format_definitions(self, lsp_locations: List[Dict]) -> List[Dict[str, Any]]:
        """
        Format LSP definition results
        
        Args:
            lsp_locations: List of LSP location objects
            
        Returns:
            List of formatted definition results
        """
        formatted = []
        
        for location in lsp_locations:
            try:
                uri = location['uri']
                range_info = location['range']
                
                file_path = self._uri_to_path(uri)
                line_num = range_info['start']['line']
                
                # Get multi-line context for definitions
                context = self._get_file_context(file_path, line_num, 3)
                
                formatted.append({
                    'file': str(file_path.relative_to(self.repo_path)),
                    'line': line_num + 1,  # 1-indexed for display
                    'column': range_info['start']['character'],
                    'context': context,
                    'type': 'definition'
                })
                
            except Exception as e:
                print(f"Error formatting definition: {e}")
                continue
                
        return formatted
    
    def format_document_symbols(self, symbols: List[Dict], file_path: str) -> List[Dict[str, Any]]:
        """
        Format document symbols for file exploration
        
        Args:
            symbols: List of LSP document symbols
            file_path: Relative path to the file
            
        Returns:
            List of formatted symbol information
        """
        formatted = []
        
        def process_symbol(symbol: Dict, parent_name: str = ""):
            try:
                name = symbol['name']
                kind = symbol.get('kind', 1)
                range_info = symbol['range']
                
                full_name = f"{parent_name}.{name}" if parent_name else name
                
                formatted.append({
                    'file': file_path,
                    'line': range_info['start']['line'] + 1,  # 1-indexed
                    'column': range_info['start']['character'],
                    'name': name,
                    'full_name': full_name,
                    'kind': self._format_symbol_kind(kind),
                    'type': 'definition'
                })
                
                # Process nested symbols (e.g., methods in classes)
                if 'children' in symbol:
                    for child in symbol['children']:
                        process_symbol(child, full_name)
                        
            except Exception as e:
                print(f"Error processing symbol: {e}")
        
        for symbol in symbols:
            process_symbol(symbol)
            
        return formatted
    
    def _uri_to_path(self, uri: str) -> Path:
        """Convert file URI to Path object"""
        if uri.startswith('file://'):
            return Path(uri[7:])  # Remove 'file://' prefix
        return Path(uri)
    
    def _format_symbol_kind(self, kind: int) -> str:
        """Convert LSP symbol kind number to string"""
        # LSP SymbolKind enumeration
        kinds = {
            1: "File", 2: "Module", 3: "Namespace", 4: "Package", 5: "Class",
            6: "Method", 7: "Property", 8: "Field", 9: "Constructor", 10: "Enum",
            11: "Interface", 12: "Function", 13: "Variable", 14: "Constant",
            15: "String", 16: "Number", 17: "Boolean", 18: "Array", 19: "Object",
            20: "Key", 21: "Null", 22: "EnumMember", 23: "Struct", 24: "Event",
            25: "Operator", 26: "TypeParameter"
        }
        return kinds.get(kind, "Unknown")
    
    def _get_file_context(self, file_path: Path, center_line: int, context_lines: int) -> str:
        """
        Get multiple lines of context around target line
        
        Args:
            file_path: Path to file
            center_line: 0-indexed line number to center on
            context_lines: Number of lines before and after to include
            
        Returns:
            Context string with multiple lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            start = max(0, center_line - context_lines)
            end = min(len(lines), center_line + context_lines + 1)
            
            context = ''.join(lines[start:end]).rstrip()
            return context
            
        except Exception as e:
            print(f"Error reading context from {file_path}: {e}")
            return ""
    
    def _get_single_line_context(self, file_path: Path, line_num: int) -> str:
        """
        Get single line context
        
        Args:
            file_path: Path to file
            line_num: 0-indexed line number
            
        Returns:
            Single line of code as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if 0 <= line_num < len(lines):
                return lines[line_num].strip()
            return ""
            
        except Exception as e:
            print(f"Error reading line from {file_path}: {e}")
            return ""