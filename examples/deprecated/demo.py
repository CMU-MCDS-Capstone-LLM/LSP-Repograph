#!/usr/bin/env python3
"""
Interactive REPL demo for LSP-based code search tool
Demonstrates where_used and where_defined functionality
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lsp_repograph.tools.simple_code_tool import SimpleCodeTool
from lsp_repograph.utils.file_utils import create_sample_project


def main():
    print("=== LSP-based Code Search Tool Demo ===")
    print()
    
    # Create sample project
    print("Setting up sample project...")
    sample_path = create_sample_project()
    print(f"✓ Sample project created at: {sample_path}")
    print()
    
    # Initialize tool
    try:
        tool = SimpleCodeTool(sample_path)
        print()
    except Exception as e:
        print(f"Error initializing tool: {e}")
        print("Make sure you have pyright installed: pip install pyright")
        return
    
    print("Available commands:")
    print("  def <symbol>    - Find definitions")
    print("  use <symbol>    - Find usages/references") 
    print("  both <symbol>   - Find both definitions and usages")
    print("  explore <file>  - Show all symbols in a file")
    print("  pos <file> <line> <col> - Find symbol at position")
    print("  help           - Show this help")
    print("  quit           - Exit")
    print()
    print("Try these examples:")
    print("  def Calculator")
    print("  use calculate_sum")
    print("  both AdvancedCalculator")
    print("  explore math_utils.py")
    print()
    
    while True:
        try:
            command = input("lsp> ").strip().split()
            
            if not command:
                continue
                
            if command[0] == "quit":
                break
            elif command[0] == "help":
                show_help()
                continue
                
            if command[0] == "def" and len(command) == 2:
                symbol = command[1]
                results = tool.where_defined(symbol)
                print_results(f"Definitions of '{symbol}'", results)
                
            elif command[0] == "use" and len(command) == 2:
                symbol = command[1]
                results = tool.where_used(symbol)
                print_results(f"Usages of '{symbol}'", results)
                
            elif command[0] == "both" and len(command) == 2:
                symbol = command[1]
                search_results = tool.search_symbol(symbol)
                print_results(f"Definitions of '{symbol}'", search_results['definitions'])
                print_results(f"References to '{symbol}'", search_results['references'])
                
            elif command[0] == "explore" and len(command) == 2:
                file_path = command[1]
                results = tool.explore_file(file_path)
                print_results(f"Symbols in '{file_path}'", results)
                
            elif command[0] == "pos" and len(command) == 4:
                file_path, line_str, col_str = command[1], command[2], command[3]
                try:
                    line, col = int(line_str), int(col_str)
                    result = tool.find_symbol_at_position(file_path, line, col)
                    print_results(f"Symbol at {file_path}:{line}:{col} - Definitions", 
                                result['definitions'])
                    print_results(f"Symbol at {file_path}:{line}:{col} - References", 
                                result['references'])
                except ValueError:
                    print("Error: Line and column must be numbers")
                    
            else:
                print("Invalid command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nShutting down...")
    tool.shutdown()
    print("Goodbye!")


def show_help():
    """Show detailed help information"""
    print("""
Command syntax:
  def <symbol>         - Find where a symbol is defined
  use <symbol>         - Find where a symbol is used/referenced
  both <symbol>        - Show both definitions and references
  explore <file>       - List all symbols defined in a file
  pos <file> <L> <C>   - Find symbol at line L, column C in file
  
Examples:
  def Calculator              # Find Calculator class definition
  use calculate_sum           # Find all uses of calculate_sum function
  both AdvancedCalculator     # Find definition and all uses
  explore math_utils.py       # Show all classes/functions in file
  pos main.py 15 8            # Find symbol at line 15, column 8
  
Available symbols in sample project:
  - Calculator (class)
  - AdvancedCalculator (class)
  - calculate_sum (function)
  - calculate_product (function)
  - DataProcessor (class)
  - main (function)
    """)


def print_results(title: str, results: list):
    """Print search results in a nice format"""
    print(f"\n=== {title} ===")
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        symbol_info = ""
        if 'symbol_kind' in result and 'name' in result:
            symbol_info = f" ({result['symbol_kind']}: {result['name']})"
        elif 'kind' in result:
            symbol_info = f" ({result['kind']})"
            
        print(f"\n{i}. {result['file']}:{result['line']}{symbol_info}")
        
        # Show context with some formatting
        context = result.get('context', '').strip()
        if context:
            # Indent context for better readability
            context_lines = context.split('\n')
            for line in context_lines:
                print(f"   {line}")
        
        # Show additional info if available
        if 'container_name' in result and result['container_name']:
            print(f"   └─ Container: {result['container_name']}")


if __name__ == "__main__":
    main()