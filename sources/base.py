from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLeadSource(ABC):
    """
    Abstract Base Class for Lead Ingestion Sources.
    Ensures modularity: Manual Entry, CSV Import, and future approved API sources
    can be plugged in without changing the core business logic or UI.
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source provider."""
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Whether this source is currently active and authorized."""
        pass

    @abstractmethod
    def parse_discussion(self, raw_input: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Parse raw text/discussion into structured lead parameters."""
        pass
