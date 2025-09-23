from abc import ABC, abstractmethod
from typing import List
from lsp_repograph.core.multilspy_client import MultilspyLSPClient


class Command(ABC):
    """Abstract base class for demo commands"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name used for dispatch"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for help"""
        pass
    
    @property
    @abstractmethod
    def usage(self) -> str:
        """Usage string showing syntax"""
        pass
    
    @property
    @abstractmethod
    def example(self) -> str:
        """Example command for help"""
        pass
    
    @abstractmethod
    def execute(self, client: MultilspyLSPClient, args: List[str]) -> None:
        """Execute the command with the given client and arguments"""
        pass