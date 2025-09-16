"""
Pyright LSP client for semantic code analysis
Handles JSON-RPC communication with Pyright language server
"""

import subprocess
import json
import threading
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class PyrightLSPClient:
    """
    LSP client focused on leveraging Pyright's built-in capabilities
    No text scanning - pure LSP approach for maximum performance
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.request_id = 0
        self.request_lock = threading.Lock()
        self.pending_requests = {}  # Track pending requests by ID
        self.server = None
        
        # Start Pyright LSP server
        self._start_server()
        
        # Initialize LSP session
        self._initialize()
    
    def _start_server(self):
        """Start Pyright LSP server process"""
        try:
            self.server = subprocess.Popen([
                    # 'pyright-langserver', '--stdio'
                    'jedi-language-server'
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Start response reader thread
            self.reader_thread = threading.Thread(target=self._read_responses)
            self.reader_thread.daemon = True
            self.reader_thread.start()
            
        except FileNotFoundError:
            raise RuntimeError(
                "pyright-langserver not found. Install with: pip install pyright"
            )
    
    def _initialize(self):
        """Initialize LSP connection with enhanced capabilities"""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "workspaceFolders": [
                    {"uri": self.repo_path.as_uri(), "name": self.repo_path.name}
                ],
                # "capabilities": {
                #     "textDocument": {
                #         "synchronization": {
                #         "dynamicRegistration": False,
                #         "willSave": False,
                #         "didSave": True
                #         }
                #     },
                #     "workspace": {
                #         "didChangeWatchedFiles": { "dynamicRegistration": True },
                #         "workspaceFolders": True,
                #         "configuration": True
                #     }
                # },
                "initializationOptions": {
                    "settings": {
                        "python": {
                            "analysis": {
                                "diagnosticMode": "workspace"
                            }
                        }
                    }
                }
            }
        }
        
        response = self._send_request(init_request)
        
        # Send initialized notification
        self._send_notification({
            "jsonrpc": "2.0",
            "method": "initialized", 
            "params": {}
        })
        
        # Give server time to initialize
        time.sleep(1)
    
    def workspace_symbol_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols across entire workspace using LSP
        This replaces text-scanning approach for much better performance
        
        Args:
            query: Symbol name to search for
            
        Returns:
            List of symbol information with location
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "workspace/symbol",
            "params": {
                "query": query
            }
        }
        
        response = self._send_request(request)
        return response if isinstance(response, list) else []
    
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
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "textDocument/definition",
            "params": {
                "textDocument": {"uri": Path(file_path).as_uri()},
                "position": {"line": line, "character": character}
            }
        }
        
        response = self._send_request(request)
        return response if isinstance(response, list) else []
    
    def get_references(self, file_path: str, line: int, character: int, 
                      include_declaration: bool = True) -> List[Dict[str, Any]]:
        """
        Get all references to symbol at position
        
        Args:
            file_path: Absolute path to file
            line: 0-indexed line number  
            character: 0-indexed character position
            include_declaration: Include the definition in results
            
        Returns:
            List of location dictionaries
        """
        request = {
            "jsonrpc": "2.0", 
            "id": self._next_id(),
            "method": "textDocument/references",
            "params": {
                "textDocument": {"uri": Path(file_path).as_uri()},
                "position": {"line": line, "character": character},
                "context": {"includeDeclaration": include_declaration}
            }
        }
        
        response = self._send_request(request)
        return response if isinstance(response, list) else []
    
    def get_document_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all symbols defined in a document
        Useful for building indices or exploring file structure
        
        Args:
            file_path: Absolute path to file
            
        Returns:
            List of document symbols
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(), 
            "method": "textDocument/documentSymbol",
            "params": {
                "textDocument": {"uri": Path(file_path).as_uri()}
            }
        }
        
        response = self._send_request(request)
        return response if isinstance(response, list) else []
    
    def _send_request(self, request: Dict) -> Optional[Any]:
        """Send JSON-RPC request and wait for response"""
        if not self.server or self.server.poll() is not None:
            print("LSP server is not running")
            return None
            
        request_id = request.get('id')
        response_event = threading.Event()
        
        # Register pending request
        if request_id is not None:
            self.pending_requests[request_id] = {
                'event': response_event,
                'response': None
            }
        
        with self.request_lock:
            try:
                request_str = json.dumps(request)
                content_length = len(request_str.encode('utf-8'))
                
                message = f"Content-Length: {content_length}\r\n\r\n{request_str}"
                
                print(f"LSP: Sending request: {request_str}.")  # Debug output
                
                self.server.stdin.write(message)
                self.server.stdin.flush()
                
                if request_id is None:
                    return None  # Notification, no response expected
                
                # Wait for response
                print(f"LSP: Waiting for response to request {request_id}...")
                if response_event.wait(timeout=30.0):
                    pending = self.pending_requests.pop(request_id, {})
                    response = pending.get('response')
                    
                    if response and 'result' in response:
                        print(f"LSP: Got successful response for request {request_id}.")
                        return response['result']
                    elif response and 'error' in response:
                        print(f"LSP error: {response['error']}.")
                        return None
                else:
                    print(f"LSP request {request_id} timed out")
                    self.pending_requests.pop(request_id, None)
                    return None
                    
            except Exception as e:
                print(f"LSP request failed: {e}")
                self.pending_requests.pop(request_id, None)
                return None
    
    def _send_notification(self, notification: Dict):
        """Send notification (no response expected)"""
        self._send_request(notification)
    
    def _read_responses(self):
        """Read LSP responses in background thread"""
        while self.server and self.server.poll() is None:
            try:
                # Read Content-Length header
                header = self.server.stdout.readline()
                print("header: ", header.__repr__())
                if not header:
                    print("LSP: No header received, server might be dead")
                    break
                    
                if not header.startswith("Content-Length:"):
                    print(f"LSP: Unexpected header: {header.strip()}")
                    continue
                    
                length = int(header.split(":")[1].strip())
                
                # Skip empty line
                empty_line = self.server.stdout.readline()
                print("empty line: ", empty_line.__repr__())
                
                # Read JSON content
                content = self.server.stdout.read(length)
                print("content: ", content.__repr__())
                if not content:
                    print("LSP: No content received")
                    break
                
                print(f"LSP: Received response: {content}.")  # Debug output
                    
                response = json.loads(content)
                
                # Handle response
                response_id = response.get('id')
                if response_id is not None and response_id in self.pending_requests:
                    pending = self.pending_requests[response_id]
                    pending['response'] = response
                    pending['event'].set()
                else:
                    print(f"LSP: Received response for unknown request ID: {response_id}")
                
            except Exception as e:
                print(f"Error reading LSP response: {e}")
                # Print stderr for debugging
                if self.server and self.server.stderr:
                    try:
                        stderr_content = self.server.stderr.read()
                        if stderr_content:
                            print(f"LSP stderr: {stderr_content}")
                    except:
                        pass
                break
    
    def _next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def shutdown(self):
        """Cleanly shutdown LSP server"""
        if not self.server:
            return
            
        try:
            # Send shutdown request
            shutdown_request = {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "shutdown",
                "params": None
            }
            self._send_request(shutdown_request)
            
            # Send exit notification
            exit_notification = {
                "jsonrpc": "2.0",
                "method": "exit",
                "params": None
            }
            self._send_notification(exit_notification)
            
            # Give server time to shutdown gracefully
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error during LSP shutdown: {e}")
        finally:
            # Force terminate if still running
            if self.server.poll() is None:
                self.server.terminate()
                self.server.wait(timeout=5)
    
    def __del__(self):
        """Cleanup on destruction"""
        self.shutdown()