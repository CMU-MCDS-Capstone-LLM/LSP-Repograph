#!/usr/bin/env python3
"""
Demo REPL for JediLSPClient using multilspy
Provides interactive access to the three core APIs
"""

import sys
import os
from pathlib import Path
from pprint import pprint

# Add parent directory to path to import lsp_repograph
sys.path.insert(0, str(Path(__file__).parent.parent))

from lsp_repograph.core.multilspy_client import MultilspyLSPClient
from typing import Dict, Any


def read_file_line(file_path: str, line_number: int) -> str:
    """Read a specific line from a file (0-indexed)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if 0 <= line_number < len(lines):
                return lines[line_number].rstrip()
    except Exception as e:
        return f"<Error reading file: {e}>"
    return "<Line not found>"


def format_reference_with_content(ref: Dict[str, Any], repo_path: str) -> str:
    """Format a reference with its source line content"""
    # Extract file path (prefer absolutePath, fallback to relativePath)
    if 'absolutePath' in ref:
        file_path = ref['absolutePath']
        rel_path = os.path.relpath(file_path, repo_path)
    elif 'relativePath' in ref:
        rel_path = ref['relativePath'] 
        file_path = os.path.join(repo_path, rel_path)
    else:
        return str(ref)  # Fallback to raw output
    
    # Extract line/column info
    range_info = ref.get('range', {})
    start = range_info.get('start', {})
    line_num = start.get('line', 0)  # 0-indexed
    col_num = start.get('character', 0)
    
    # Read the actual line content
    line_content = read_file_line(file_path, line_num)
    
    # Format output
    return f"{rel_path}:{line_num + 1}:{col_num + 1}: {line_content}"


def print_help():
    """Print available commands"""
    print("\n=== MultilspyLSPClient Demo REPL ===")
    print("Commands:")
    print("  find-ws-def <query>            - Find workspace symbol definitions (this excludes symbols from third-party / standard library, and built-ins)")
    print("  find-ws-refs <query>           - Find workspace symbol references (<query> must uniquely identify a symbol in workspace)")
    print("  find-lib-def <library> [symbol] - Find library symbol definitions")
    print("  find-lib-refs <library> [symbol] - Find library symbol references")
    print("  find-builtin-def [symbol]      - Find builtin symbol definitions")
    print("  find-builtin-refs [symbol]     - Find builtin symbol references")
    print("  find-def-at-pos <file> <line> <col> - Find definition at position")
    print("  find-refs-at-pos <file> <line> <col> - Find references at position")
    print("  help                          - Show this help")
    print("  quit / exit                   - Exit REPL")
    print("\nFile paths should be relative to the repo root.")
    print("Line and column numbers are 0-indexed.")
    print("Examples:")
    print("  find-ws-def AdvancedCalculator")
    print("  find-ws-refs core.math_utils.Calculator.add")
    print("  find-lib-def os.path join")
    print("  find-lib-refs os.path join")
    print("  find-builtin-def int")
    print("  find-builtin-refs print")
    print("  find-def-at-pos main.py 4 40")
    print("  find-refs-at-pos main.py 4 40")


def main():
    # Use sample_project as default repo
    # repo_path = os.path.join(os.path.dirname(__file__), "sample_project")
    repo_path = os.path.join(os.path.dirname(__file__), "sample_project_no_venv")
    # repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/twisted_twisted_e31995c9_parent"
    # repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/ovirt_vdsm_6eef802a_parent"
    # repo_path = "/home/eiger/CMU/2025_Spring/11634_Capstone/playground/pymigbench/repos/toufool_auto-split_86244b6c_parent"
    
    if not os.path.exists(repo_path):
        print(f"Error: Sample project not found at {repo_path}")
        return
    
    print(f"Initializing JediLSPClient for repo: {repo_path}")
    
    try:
        client = MultilspyLSPClient(repo_path)
        print("Client initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize client: {e}")
        return
    
    print_help()
    
    while True:
        try:
            command = input("\n>>> ").strip()
            
            if not command:
                continue
                
            if command in ['quit', 'exit']:
                break
                
            if command == 'help':
                print_help()
                continue
            
            parts = command.split()
            
            if len(parts) == 0:
                continue
                
            cmd = parts[0].lower()
            
            if cmd == 'find-ws-def':
                if len(parts) < 2:
                    print("Usage: find-ws-def <query>")
                    continue
                    
                query = ' '.join(parts[1:])
                print(f"Searching workspace symbols for: '{query}'")
                
                result = client.search_ws_symbol_def(query)
                print(f"\nFound {len(result)} workspace symbols:")
                pprint(result)
                
            elif cmd == 'find-ws-refs':
                if len(parts) < 2:
                    print("Usage: find-ws-refs <query>")
                    continue
                    
                query = ' '.join(parts[1:])
                print(f"Searching workspace symbol references for: '{query}'")
                
                result = client.find_ws_symbol_refs(query)
                print(f"\nFound {len(result)} workspace symbol references:")
                if result:
                    for ref in result:
                        print(format_reference_with_content(ref, repo_path))
                else:
                    print("No references found.")
                
            elif cmd == 'find-lib-def':
                if len(parts) < 2:
                    print("Usage: find-lib-def <library> [symbol]")
                    continue
                    
                library = parts[1]
                symbol = parts[2] if len(parts) > 2 else None
                
                if symbol:
                    print(f"Searching for symbol '{symbol}' in library '{library}'")
                else:
                    print(f"Searching for library '{library}' definition")
                
                result = client.search_non_workspace_library_symbol(library, symbol)
                print(f"\nFound {len(result)} library symbols:")
                pprint(result)
                
            elif cmd == 'find-builtin-def':
                symbol = parts[1] if len(parts) > 1 else None
                
                if symbol:
                    print(f"Searching for builtin symbol '{symbol}'")
                else:
                    print("Searching for builtins module definition")
                
                result = client.search_builtins_symbol_def(symbol)
                print(f"\nFound {len(result)} builtin symbols:")
                pprint(result)
                
            elif cmd == 'find-lib-refs':
                if len(parts) < 2:
                    print("Usage: find-lib-refs <library> [symbol]")
                    continue
                    
                library = parts[1]
                symbol = parts[2] if len(parts) > 2 else None
                
                if symbol:
                    print(f"Searching for references to symbol '{symbol}' in library '{library}'")
                else:
                    print(f"Searching for references to library '{library}'")
                
                result = client.find_non_workspace_library_symbol_refs(library, symbol)
                print(f"\nFound {len(result)} library symbol references:")
                if result:
                    for ref in result:
                        print(format_reference_with_content(ref, repo_path))
                else:
                    print("No references found.")
                
            elif cmd == 'find-builtin-refs':
                symbol = parts[1] if len(parts) > 1 else None
                
                if symbol:
                    print(f"Searching for references to builtin symbol '{symbol}'")
                else:
                    print("Searching for references to builtins module")
                
                result = client.find_builtins_symbol_refs(symbol)
                print(f"\nFound {len(result)} builtin symbol references:")
                if result:
                    for ref in result:
                        print(format_reference_with_content(ref, repo_path))
                else:
                    print("No references found.")
                
            elif cmd == 'find-def-at-pos':
                if len(parts) < 4:
                    print("Usage: find-def-at-pos <file> <line> <col>")
                    continue
                    
                try:
                    file_path = parts[1]
                    line = int(parts[2])
                    col = int(parts[3])
                    
                    # Convert relative path to absolute
                    abs_path = os.path.join(repo_path, file_path)
                    
                    if not os.path.exists(abs_path):
                        print(f"File not found: {file_path}")
                        continue
                    
                    print(f"Finding definition at {file_path}:{line}:{col}")
                    
                    result = client.find_definition(abs_path, line, col)
                    print(f"\nFound {len(result)} definitions:")
                    pprint(result)
                    
                except ValueError:
                    print("Line and column must be integers")
                except Exception as e:
                    print(f"Error: {e}")
                    
            elif cmd == 'find-refs-at-pos':
                if len(parts) < 4:
                    print("Usage: find-refs-at-pos <file> <line> <col>")
                    continue
                    
                try:
                    file_path = parts[1]
                    line = int(parts[2])
                    col = int(parts[3])
                    
                    # Convert relative path to absolute
                    abs_path = os.path.join(repo_path, file_path)
                    
                    if not os.path.exists(abs_path):
                        print(f"File not found: {file_path}")
                        continue
                    
                    print(f"Finding references at {file_path}:{line}:{col}")
                    
                    result = client.find_references(abs_path, line, col)
                    print(f"\nFound {len(result)} references:")
                    if result:
                        for ref in result:
                            print(format_reference_with_content(ref, repo_path))
                    else:
                        print("No references found.")
                    
                except ValueError:
                    print("Line and column must be integers")
                except Exception as e:
                    print(f"Error: {e}")
                    
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Shutting down client...")
    client.shutdown()
    print("Goodbye!")


if __name__ == "__main__":
    main()
