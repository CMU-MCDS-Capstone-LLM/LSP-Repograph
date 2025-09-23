import os
from typing import List
from pprint import pprint
from .base import Command
from .utils import format_reference_with_content
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class FindDefinitionAtPositionCommand(Command):
    """Find definition at position"""
    
    @property
    def name(self) -> str:
        return "find-def-at-pos"
    
    @property
    def description(self) -> str:
        return "Find definition at position"
    
    @property
    def usage(self) -> str:
        return "find-def-at-pos <file> <line> <col>"
    
    @property
    def example(self) -> str:
        return "find-def-at-pos main.py 4 40"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        if len(args) < 3:
            print(f"Usage: {self.usage}")
            return
            
        try:
            file_path = args[0]
            line = int(args[1])
            col = int(args[2])
            
            # Convert relative path to absolute using client's repo path
            if hasattr(client, 'repo_path'):
                abs_path = os.path.join(client.repo_path, file_path)
            else:
                abs_path = file_path
            
            if not os.path.exists(abs_path):
                print(f"File not found: {file_path}")
                return
            
            print(f"Finding definition at {file_path}:{line}:{col}")
            
            result = client.find_definition(abs_path, line, col)
            print(f"\nFound {len(result)} definitions:")
            pprint(result)
            
        except ValueError:
            print("Line and column must be integers")
        except Exception as e:
            print(f"Error: {e}")


class FindReferencesAtPositionCommand(Command):
    """Find references at position"""
    
    @property
    def name(self) -> str:
        return "find-refs-at-pos"
    
    @property
    def description(self) -> str:
        return "Find references at position"
    
    @property
    def usage(self) -> str:
        return "find-refs-at-pos <file> <line> <col>"
    
    @property
    def example(self) -> str:
        return "find-refs-at-pos main.py 4 40"
    
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        if len(args) < 3:
            print(f"Usage: {self.usage}")
            return
            
        try:
            file_path = args[0]
            line = int(args[1])
            col = int(args[2])
            
            # Convert relative path to absolute using client's repo path
            if hasattr(client, 'repo_path'):
                abs_path = os.path.join(client.repo_path, file_path)
            else:
                abs_path = file_path
            
            if not os.path.exists(abs_path):
                print(f"File not found: {file_path}")
                return
            
            print(f"Finding references at {file_path}:{line}:{col}")
            
            result = client.find_references(abs_path, line, col)
            print(f"\nFound {len(result)} references:")
            if result:
                for ref in result:
                    print(format_reference_with_content(ref))
            else:
                print("No references found.")
            
        except ValueError:
            print("Line and column must be integers")
        except Exception as e:
            print(f"Error: {e}")