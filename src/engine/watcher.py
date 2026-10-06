from __future__ import annotations

from pathlib import Path
from typing import Callable, List

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer


class _Handler(FileSystemEventHandler):
    def __init__(
        self,
        root: Path,
        on_change: Callable[[str], None],
        on_delete: Callable[[str], None],
    ) -> None:
        self._root = root
        self._on_change = on_change
        self._on_delete = on_delete

    def _rel(self, path: str) -> str:
        try:
            return str(Path(path).relative_to(self._root)).replace("\\", "/")
        except ValueError:
            return path

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self._on_change(self._rel(event.src_path))

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self._on_change(self._rel(event.src_path))

    def on_deleted(self, event: FileDeletedEvent) -> None:
        if not event.is_directory:
            self._on_delete(self._rel(event.src_path))

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory:
            self._on_delete(self._rel(event.src_path))
            self._on_change(self._rel(event.dest_path))


class FileWatcher:
    def __init__(
        self,
        local_root: str,
        on_change: Callable[[str], None],
        on_delete: Callable[[str], None],
    ) -> None:
        self._observer = Observer()
        handler = _Handler(Path(local_root), on_change, on_delete)
        self._observer.schedule(handler, local_root, recursive=True)

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join()
