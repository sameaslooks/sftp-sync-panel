from __future__ import annotations

import os
import posixpath
from datetime import datetime
from typing import Callable, List, Optional

from .differ import SyncOp, OpType

TRASH_DIR = ".synctool-trash"


class SyncExecutor:
    def __init__(
        self,
        conn,
        local_root: str,
        remote_root: str,
        on_progress: Optional[Callable[[int, int, SyncOp], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        self.conn = conn
        self.local_root = local_root
        self.remote_root = remote_root
        self._on_progress = on_progress or (lambda *a: None)
        self._on_log = on_log or (lambda *a: None)
        self._remote_dir_cache: set[str] = set()

    # ------------------------------------------------------------------
    def execute(self, ops: List[SyncOp], dry_run: bool = False) -> None:
        total = len(ops)
        for i, op in enumerate(ops):
            if op.op == OpType.DELETE:
                self._delete(op, dry_run)
            else:
                self._upload(op, dry_run)
            self._on_progress(i + 1, total, op)

    # ------------------------------------------------------------------
    def _upload(self, op: SyncOp, dry_run: bool) -> None:
        local_path = os.path.join(self.local_root, op.path.replace("/", os.sep))
        remote_path = posixpath.join(self.remote_root, op.path)

        if dry_run:
            self._on_log(f"[dry-run] upload {op.path}", "info")
            return

        self._ensure_remote_dir(posixpath.dirname(remote_path))

        try:
            file_size = os.path.getsize(local_path)
            self.conn.sftp.put(local_path, remote_path)
            st = os.stat(local_path)
            self.conn.sftp.utime(remote_path, (st.st_atime, st.st_mtime))
            self._on_log(f"✓ {op.path}  ({_fmt(file_size)})", "success")
        except Exception as e:
            self._on_log(f"✗ {op.path}: {e}", "error")

    def _delete(self, op: SyncOp, dry_run: bool) -> None:
        remote_path = posixpath.join(self.remote_root, op.path)
        date_str = datetime.now().strftime("%Y-%m-%d")
        trash_path = posixpath.join(self.remote_root, TRASH_DIR, date_str, op.path)

        if dry_run:
            self._on_log(f"[dry-run] trash {op.path}", "warning")
            return

        try:
            self._ensure_remote_dir(posixpath.dirname(trash_path))
            self.conn.sftp.rename(remote_path, trash_path)
            self._on_log(f"🗑 {op.path} → {TRASH_DIR}/{date_str}/", "warning")
        except Exception as e:
            self._on_log(f"✗ delete {op.path}: {e}", "error")

    # ------------------------------------------------------------------
    def _ensure_remote_dir(self, remote_dir: str) -> None:
        if remote_dir in self._remote_dir_cache:
            return
        parts = remote_dir.lstrip("/").split("/")
        current = "/" if remote_dir.startswith("/") else ""
        for part in parts:
            if not part:
                continue
            current = posixpath.join(current, part)
            if current in self._remote_dir_cache:
                continue
            try:
                self.conn.sftp.stat(current)
            except FileNotFoundError:
                self.conn.sftp.mkdir(current)
            self._remote_dir_cache.add(current)


def _fmt(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n //= 1024
    return f"{n:.1f} TB"
