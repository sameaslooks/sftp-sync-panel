from __future__ import annotations

from typing import Dict, Optional

from .connection import SFTPConnection


class ConnectionPool:
    def __init__(self) -> None:
        self._conns: Dict[str, SFTPConnection] = {}

    def get(self, name: str) -> Optional[SFTPConnection]:
        return self._conns.get(name)

    def set(self, name: str, conn: SFTPConnection) -> None:
        self._conns[name] = conn

    def remove(self, name: str) -> None:
        conn = self._conns.pop(name, None)
        if conn:
            conn.disconnect()

    def is_connected(self, name: str) -> bool:
        conn = self._conns.get(name)
        return conn is not None and conn.is_connected()

    def disconnect_all(self) -> None:
        for conn in list(self._conns.values()):
            conn.disconnect()
        self._conns.clear()

    def active_names(self) -> list[str]:
        return [n for n, c in self._conns.items() if c.is_connected()]


POOL = ConnectionPool()
