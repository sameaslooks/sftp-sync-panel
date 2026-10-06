from __future__ import annotations

from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from config import Profile
from engine.connection import SFTPConnection
from engine.differ import FileInfo, FileTree, SyncOp, compute_diff
from engine.watcher import FileWatcher
from gui.filepanel import FilePanel
from gui.logpanel import LogPanel
from gui.notificationstrip import NotificationStrip
from gui.workers import ConnectWorker, DeleteWorker, LocalScanWorker, ScanWorker, SyncWorker
import gui.theme as theme


class SyncTab(QWidget):
    connection_state_changed = pyqtSignal()
    disconnect_requested = pyqtSignal()
    # Watchdog fires from a background thread; these signals marshal to the main thread.
    _watcher_changed = pyqtSignal(str)
    _watcher_deleted = pyqtSignal(str)

    def __init__(self, profile: Profile, parent=None) -> None:
        super().__init__(parent)
        self.profile = profile
        self._conn: Optional[SFTPConnection] = None
        self._local_files: FileTree = {}
        self._remote_files: FileTree = {}
        self._watcher: Optional[FileWatcher] = None
        self._pending_changes: set[str] = set()
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_debounce_fire)

        self._connect_worker: Optional[ConnectWorker] = None
        self._scan_worker: Optional[ScanWorker] = None
        self._local_scan_worker: Optional[LocalScanWorker] = None
        self._sync_worker: Optional[SyncWorker] = None
        self._auto_sync_after_scan: bool = False
        self._last_ops: List[SyncOp] = []
        self._last_dry_run: bool = False

        self._watcher_changed.connect(self._on_file_changed)
        self._watcher_deleted.connect(self._on_file_deleted_locally)

        self._setup_ui()

    # ── UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        self._notif_strip = NotificationStrip()
        self._notif_strip.delete_requested.connect(self._on_delete_requested)
        self._notif_strip.dismissed.connect(lambda p: self._log(f"Kept remote: {p}", "info"))
        root.addWidget(self._notif_strip)

        # Main splitter — file panels (top) / bottom panels
        main_split = QSplitter(Qt.Orientation.Vertical)
        main_split.setHandleWidth(1)

        # File panels
        panels_split = QSplitter(Qt.Orientation.Horizontal)
        panels_split.setHandleWidth(1)
        self._local_panel = FilePanel("Local")
        self._local_panel.set_path(self.profile.local_path)
        self._remote_panel = FilePanel("Remote")
        self._remote_panel.set_path(self.profile.remote_path)
        panels_split.addWidget(self._local_panel)
        panels_split.addWidget(self._remote_panel)
        panels_split.setStretchFactor(0, 1)
        panels_split.setStretchFactor(1, 1)
        main_split.addWidget(panels_split)

        # Bottom — exclusions + log
        bottom_split = QSplitter(Qt.Orientation.Horizontal)
        bottom_split.setHandleWidth(1)
        bottom_split.addWidget(self._build_exclusions_panel())
        self._log_panel = LogPanel()
        bottom_split.addWidget(self._log_panel)
        bottom_split.setStretchFactor(0, 0)
        bottom_split.setStretchFactor(1, 1)
        bottom_split.setSizes([180, 400])
        main_split.addWidget(bottom_split)

        main_split.setSizes([320, 210])
        root.addWidget(main_split, 1)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("toolbar")
        bar.setFixedHeight(38)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self._disc_btn = QPushButton("Disconnect")
        self._disc_btn.setProperty("danger", "true")
        self._disc_btn.clicked.connect(self.disconnect_requested.emit)

        sep1 = QWidget()
        sep1.setFixedSize(1, 20)
        sep1.setStyleSheet(f"background:{theme.border()};")

        self._sync_btn = QPushButton("Sync now")
        self._sync_btn.setProperty("accent", "true")
        self._sync_btn.setEnabled(False)
        self._sync_btn.clicked.connect(self._on_sync_clicked)

        self._upload_btn = QPushButton("Upload selected")
        self._upload_btn.setEnabled(False)

        self._rescan_btn = QPushButton("Rescan")
        self._rescan_btn.setEnabled(False)
        self._rescan_btn.clicked.connect(self._start_scan)

        sep2 = QWidget()
        sep2.setFixedSize(1, 20)
        sep2.setStyleSheet(f"background:{theme.border()};")

        self._excl_btn = QPushButton("Exclusions")
        self._excl_btn.clicked.connect(self._edit_exclusions)

        sep3 = QWidget()
        sep3.setFixedSize(1, 20)
        sep3.setStyleSheet(f"background:{theme.border()};")

        self._mode_label = QLabel("local → remote")
        self._mode_label.setStyleSheet(
            f"font-size:11px; color:{theme.muted()}; "
            f"border:1px solid {theme.border()}; border-radius:4px; padding:2px 8px;"
        )

        self._auto_label = QLabel()
        self._auto_label.setFixedHeight(22)
        self._update_auto_label()

        self._status_label = QLabel("Connecting…")
        self._status_label.setStyleSheet("font-size:11px; color:#B45309; margin-left:6px;")

        layout.addWidget(self._disc_btn)
        layout.addWidget(sep1)
        layout.addWidget(self._sync_btn)
        layout.addWidget(self._upload_btn)
        layout.addWidget(self._rescan_btn)
        layout.addWidget(sep2)
        layout.addWidget(self._excl_btn)
        layout.addWidget(sep3)
        layout.addWidget(self._mode_label)
        layout.addWidget(self._auto_label)
        layout.addStretch()
        layout.addWidget(self._status_label)

        return bar

    def _build_exclusions_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("exclusionsPanel")
        panel.setMinimumWidth(150)
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(28)
        header.setStyleSheet(
            f"background:{theme.surface()}; border-bottom:1px solid {theme.border()};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)
        title = QLabel("Exclusions")
        title.setStyleSheet(
            f"font-size:11px;font-weight:600;color:{theme.muted()};background:transparent;"
        )
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedHeight(18)
        edit_btn.setStyleSheet(
            "font-size:10px; border:none; color:#3B82F6; background:transparent; padding:0;"
        )
        edit_btn.clicked.connect(self._edit_exclusions)
        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(edit_btn)
        root.addWidget(header)

        self._excl_list = QListWidget()
        self._excl_list.setStyleSheet(
            f"QListWidget {{ border:none; background:{theme.bg()}; }}"
            f"QListWidget::item {{ font-family:Consolas,monospace; font-size:11px; "
            f"padding:3px 8px; color:{theme.muted()}; }}"
        )
        self._rebuild_excl_list()
        root.addWidget(self._excl_list, 1)

        return panel

    def _rebuild_excl_list(self) -> None:
        self._excl_list.clear()
        for exc in self.profile.exclusions:
            item = QListWidgetItem(f"⊘  {exc}")
            item.setToolTip(exc)
            self._excl_list.addItem(item)

    def _update_auto_label(self) -> None:
        if self.profile.auto_sync:
            self._auto_label.setText(f"auto-sync {self.profile.auto_sync_interval}s")
            self._auto_label.setStyleSheet(
                "font-size:11px; color:#15803D; "
                "border:1px solid #86EFAC; border-radius:4px; padding:2px 8px;"
            )
        else:
            self._auto_label.setText("auto-sync off")
            self._auto_label.setStyleSheet(
                f"font-size:11px; color:{theme.muted()}; "
                f"border:1px solid {theme.border()}; border-radius:4px; padding:2px 8px;"
            )

    # ── Connect flow ─────────────────────────────────────────────────────

    def start_connect(self) -> None:
        self._set_status("Connecting…", "#B45309")
        self._connect_worker = ConnectWorker(self.profile)
        self._connect_worker.connected.connect(self._on_connected)
        self._connect_worker.failed.connect(self._on_connect_failed)
        self._connect_worker.start()

    def _on_connected(self, conn: SFTPConnection) -> None:
        self._conn = conn
        self._set_status("Connected", "#15803D")
        self._log(f"Connected to {self.profile.host}:{self.profile.port} via {self.profile.auth}", "success")
        self._sync_btn.setEnabled(True)
        self._rescan_btn.setEnabled(True)
        self.connection_state_changed.emit()
        self._start_scan()

        if self.profile.auto_sync:
            self._start_watcher()

    def _on_connect_failed(self, msg: str) -> None:
        self._set_status("Connection failed", "#DC2626")
        self._log(f"Connection failed: {msg}", "error")
        self.connection_state_changed.emit()

    def disconnect(self) -> None:
        self._stop_watcher()
        if self._conn:
            self._conn.disconnect()
            self._conn = None
        self._sync_btn.setEnabled(False)
        self._rescan_btn.setEnabled(False)
        self._set_status("Disconnected", "#9CA3AF")
        self.connection_state_changed.emit()

    def is_connected(self) -> bool:
        return self._conn is not None and self._conn.is_connected()

    # ── Scan ─────────────────────────────────────────────────────────────

    def _start_scan(self) -> None:
        if not self._conn:
            return
        self._set_status("Scanning…", "#B45309")
        self._log("Scanning files…")
        self._scan_worker = ScanWorker(self._conn, self.profile)
        self._scan_worker.progress.connect(lambda m: self._log(m))
        self._scan_worker.finished.connect(self._on_scan_done)
        self._scan_worker.failed.connect(lambda m: self._log(f"Scan error: {m}", "error"))
        self._scan_worker.start()

    def _on_scan_done(self, local: dict, remote: dict) -> None:
        self._local_files = local
        self._remote_files = remote
        self._set_status("Connected", "#15803D")
        self._refresh_panels()
        diff = compute_diff(local, remote, compare_mode=self.profile.compare_mode)
        adds = sum(1 for o in diff if o.op.value == "add")
        upds = sum(1 for o in diff if o.op.value == "update")
        self._log(
            f"Scan complete — {len(local)} local, {len(remote)} remote, "
            f"{adds} new, {upds} changed",
            "success",
        )
        do_auto = self._auto_sync_after_scan or self.profile.auto_sync
        self._auto_sync_after_scan = False
        if do_auto and (adds or upds):
            if self._sync_worker and self._sync_worker.isRunning():
                return
            ops = compute_diff(
                local, remote,
                mirror_delete=self.profile.mirror_delete,
                compare_mode=self.profile.compare_mode,
            )
            if ops:
                self._log(f"Auto-sync: {len(ops)} op(s)…", "info")
                self._run_sync(ops)

    def _refresh_panels(self) -> None:
        diff = compute_diff(
            self._local_files,
            self._remote_files,
            compare_mode=self.profile.compare_mode,
        )
        diff_map = {op.path: op.op.value for op in diff}

        local_statuses = {
            path: diff_map.get(path, "synced") for path in self._local_files
        }
        remote_statuses = {
            path: "synced" for path in self._remote_files
        }
        for op in diff:
            if op.op.value == "delete":
                remote_statuses[op.path] = "diff"

        self._local_panel.set_files(self._local_files, local_statuses)
        self._remote_panel.set_files(self._remote_files, remote_statuses)

    # ── Sync ─────────────────────────────────────────────────────────────

    def _on_sync_clicked(self) -> None:
        if not self._conn:
            return
        ops = compute_diff(
            self._local_files,
            self._remote_files,
            mirror_delete=self.profile.mirror_delete,
            compare_mode=self.profile.compare_mode,
        )
        if not ops:
            self._log("Nothing to sync.", "info")
            return

        from gui.dialogs.syncplan import SyncPlanDialog
        dlg = SyncPlanDialog(ops, parent=self)
        if dlg.exec():
            final_ops, dry_run = dlg.result_ops()
            self._run_sync(final_ops, dry_run)

    def _run_sync(self, ops: List[SyncOp], dry_run: bool = False) -> None:
        self._last_ops = ops
        self._last_dry_run = dry_run
        self._sync_btn.setEnabled(False)
        self._set_status("Syncing…", "#B45309")
        self._sync_worker = SyncWorker(self._conn, self.profile, ops, dry_run)
        self._sync_worker.log_line.connect(self._log)
        self._sync_worker.progress.connect(
            lambda cur, tot, msg: self._log_panel.set_progress(cur, tot, msg)
        )
        self._sync_worker.finished.connect(self._on_sync_done)
        self._sync_worker.start()

    def _on_sync_done(self, success: bool, summary: str) -> None:
        self._sync_btn.setEnabled(True)
        self._log_panel.clear_progress()
        level = "success" if success else "error"
        self._log(summary, level)
        self._set_status("Connected", "#15803D")
        if success and not self._last_dry_run:
            self._apply_ops_to_remote(self._last_ops)
        else:
            self._start_scan()

    def _apply_ops_to_remote(self, ops: List[SyncOp]) -> None:
        """Update in-memory remote state after sync — avoids full rescan."""
        import copy
        for op in ops:
            if op.op.value in ("add", "update"):
                lf = self._local_files.get(op.path)
                if lf:
                    self._remote_files[op.path] = copy.copy(lf)
            elif op.op.value == "delete":
                self._remote_files.pop(op.path, None)
        self._refresh_panels()

    # ── Auto-sync / watcher ───────────────────────────────────────────────

    def _start_watcher(self) -> None:
        if not self.profile.local_path:
            return
        self._watcher = FileWatcher(
            self.profile.local_path,
            on_change=lambda p: self._watcher_changed.emit(p),
            on_delete=lambda p: self._watcher_deleted.emit(p),
        )
        self._watcher.start()
        self._log(f"Auto-sync watching {self.profile.local_path}", "info")

    def _stop_watcher(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def _on_file_changed(self, rel_path: str) -> None:
        self._pending_changes.add(rel_path)
        self._debounce_timer.start(self.profile.auto_sync_interval * 1000)

    def _on_file_deleted_locally(self, rel_path: str) -> None:
        from engine.differ import _is_excluded
        if _is_excluded(rel_path, self.profile.exclusions):
            return
        self._notif_strip.add(rel_path)

    def _on_debounce_fire(self) -> None:
        if not self._conn or not self._pending_changes:
            return
        # Drop if a scan is already in flight to avoid SSH channel overload.
        if (self._scan_worker and self._scan_worker.isRunning()) or \
           (self._local_scan_worker and self._local_scan_worker.isRunning()):
            self._debounce_timer.start(self.profile.auto_sync_interval * 1000)
            return
        paths = list(self._pending_changes)
        self._pending_changes.clear()
        self._log(f"Auto-sync: {len(paths)} file(s) changed…", "info")
        self._start_local_scan()

    def _start_local_scan(self) -> None:
        """Rescan local only; reuse cached remote — avoids SSH round-trip."""
        if not self._remote_files:
            # No remote cache yet — fall back to full scan.
            self._auto_sync_after_scan = True
            self._start_scan()
            return
        self._local_scan_worker = LocalScanWorker(self.profile)
        self._local_scan_worker.progress.connect(lambda m: self._log(m))
        self._local_scan_worker.finished.connect(self._on_local_scan_done)
        self._local_scan_worker.failed.connect(lambda m: self._log(f"Scan error: {m}", "error"))
        self._local_scan_worker.start()

    def _on_local_scan_done(self, local: dict) -> None:
        self._local_files = local
        self._refresh_panels()
        ops = compute_diff(
            local, self._remote_files,
            mirror_delete=self.profile.mirror_delete,
            compare_mode=self.profile.compare_mode,
        )
        if ops:
            if self._sync_worker and self._sync_worker.isRunning():
                return
            self._log(f"Auto-sync: {len(ops)} op(s)…", "info")
            self._run_sync(ops)

    def _on_delete_requested(self, rel_path: str) -> None:
        if not self._conn:
            return
        worker = DeleteWorker(self._conn, self.profile, rel_path)
        worker.log_line.connect(self._log)
        worker.finished.connect(
            lambda ok, p: self._log(
                f"Deleted remote: {p}" if ok else f"Delete failed: {p}", "warning" if ok else "error"
            )
        )
        worker.start()

    # ── Exclusions ────────────────────────────────────────────────────────

    def _edit_exclusions(self) -> None:
        from gui.dialogs.exclusions import ExclusionsDialog
        dlg = ExclusionsDialog(self.profile.exclusions, local_path=self.profile.local_path, parent=self)
        if dlg.exec():
            self.profile.exclusions = dlg.get_exclusions()
            self._rebuild_excl_list()
            from config import load_profiles, save_profiles
            profiles = load_profiles()
            for i, p in enumerate(profiles):
                if p.name == self.profile.name:
                    profiles[i].exclusions = self.profile.exclusions
            save_profiles(profiles)
            self._start_scan()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str) -> None:
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"font-size:11px; color:{color}; margin-left:6px;")

    def _log(self, msg: str, level: str = "info") -> None:
        self._log_panel.append(msg, level)
