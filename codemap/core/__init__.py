"""Core indexing functionality."""

from .hasher import hash_file, hash_content
from .map_store import MapStore
from .indexer import Indexer

__all__ = ["hash_file", "hash_content", "MapStore", "Indexer"]

# Optional watcher (requires watchdog)
try:
    from .watcher import CodeMapWatcher, watch_directory
    __all__.extend(["CodeMapWatcher", "watch_directory"])
except ImportError:
    pass
