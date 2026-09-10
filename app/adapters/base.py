from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any

class SourceAdapter(ABC):
    name: str
    source_type: str = "discovery"

    @abstractmethod
    def discover(self) -> Iterable[Dict[str, Any]]:
        """Return candidate records. Never mark candidates as verified."""
        raise NotImplementedError

    def normalize_candidate(self, item):
        return item
