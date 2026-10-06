from __future__ import annotations

from typing import Dict, List

from PyQt6.QtCore import QThread, pyqtSignal

from engine.connection import SFTPConnection
from engine.differ import FileInfo, SyncOp, compute_diff, scan_local, scan_remote
from engine.executor import SyncExecutor


# ---------------------------------------------------------------------------

class ConnectWorker(QThread):
    connected = pyqtSignal(object)   # SFTPConnection
    failed = pyqtSignal(str)         # error message

    def __init__(self, profile) -> None:
        super().__init__()
        self.profile = profile

    def run(self) -> None:
        try:
            conn = SFTPConnection(self.profile)
            conn.connect()
            self.connected.emit(conn)
        except Exception as exc:
            self.failed.emit(str(exc))


# ---------------------------------------------------------------------------

class ScanWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict, dict)   # local_files, remote_files
    failed = pyqtSignal(str)

    def __init__(self, conn: SFTPConnection, profile) -> None:
        super().__init__()
        self.conn = conn
        self.profile = profile

    def run(self) -> None:
        try:
            md5 = getattr(self.profile, "compare_mode", "mtime") == "md5"
            suffix = " (MD5)…" if md5 else "…"
            self.progress.emit(f"Scanning local files{suffix}")
            local: Dict[str, FileInfo] = scan_local(
                self.profile.local_path, self.profile.exclusions, compute_md5=md5
            )
            self.progress.emit(f"Local: {len(local)} files. Scanning remote{suffix}")
            remote: Dict[str, FileInfo] = scan_remote(
                self.conn, self.profile.remote_path, self.profile.exclusions, compute_md5=md5
            )
            self.progress.emit(f"Remote: {len(remote)} files.")
            self.finished.emit(local, remote)
        except Exception as exc:
            self.failed.emit(str(exc))


# ---------------------------------------------------------------------------

class SyncWorker(QThread):
    progress = pyqtSignal(int, int, str)    # current, total, message
    log_line = pyqtSignal(str, str)         # message, level
    finished = pyqtSignal(bool, str)        # success, summary

    def __init__(
        self,
        conn: SFTPConnection,
        profile,
        ops: List[SyncOp],
        dry_run: bool = False,
    ) -> None:
        super().__init__()
        self.conn = conn
        self.profile = profile
        self.ops = ops
        self.dry_run = dry_run

    def run(self) -> None:
        def on_progress(current: int, total: int, op: SyncOp) -> None:
            self.progress.emit(current, total, op.description())

        def on_log(msg: str, level: str = "info") -> None:
            self.log_line.emit(msg, level)

        try:
            executor = SyncExecutor(
                self.conn,
                self.profile.local_path,
                self.profile.remote_path,
                on_progress=on_progress,
                on_log=on_log,
            )
            executor.execute(self.ops, dry_run=self.dry_run)
            verb = "Dry-run" if self.dry_run else "Synced"
            self.finished.emit(True, f"{verb}: {len(self.ops)} operations")
        except Exception as exc:
            self.finished.emit(False, str(exc))


# ---------------------------------------------------------------------------

class DeleteWorker(QThread):
    """Moves a single remote file to server-side trash."""
    log_line = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, conn: SFTPConnection, profile, remote_rel_path: str) -> None:
        super().__init__()
        self.conn = conn
        self.profile = profile
        self.path = remote_rel_path

    def run(self) -> None:
        from engine.differ import SyncOp, OpType, FileInfo
        op = SyncOp(OpType.DELETE, self.path, remote=FileInfo(self.path, 0, 0))
        executor = SyncExecutor(
            self.conn,
            self.profile.local_path,
            self.profile.remote_path,
            on_log=lambda m, l: self.log_line.emit(m, l),
        )
        try:
            executor.execute([op])
            self.finished.emit(True, self.path)
        except Exception as exc:
            self.finished.emit(False, str(exc))
