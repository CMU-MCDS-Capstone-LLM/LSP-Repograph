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


def print_help():
    """Print available commands"""
    print("\n=== JediLSPClient Demo REPL ===")
    print("Commands:")
    print("  search <query>                 - Search for symbols")
    print("  def <file> <line> <col>       - Find definition at position")
    print("  refs <file> <line> <col>      - Find references at position") 
    print("  help                          - Show this help")
    print("  quit / exit                   - Exit REPL")
    print("\nFile paths should be relative to the repo root.")
    print("Line and column numbers are 0-indexed.")
    print("Example: def main.py 4 40")


def main():
    # Use sample_project as default repo
    repo_path = os.path.join(os.path.dirname(__file__), "sample_project")
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
            
            if cmd == 'search':
                if len(parts) < 2:
                    print("Usage: search <query>")
                    continue
                    
                query = ' '.join(parts[1:])
                print(f"Searching for: '{query}'")
                
                result = client.search_symbol(query)
                print(f"\nFound {len(result)} symbols:")
                pprint(result)
                
            elif cmd == 'def':
                if len(parts) < 4:
                    print("Usage: def <file> <line> <col>")
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
                    
            elif cmd == 'refs':
                if len(parts) < 4:
                    print("Usage: refs <file> <line> <col>")
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
                    pprint(result)
                    
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