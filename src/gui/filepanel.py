from __future__ import annotations

from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from engine.differ import FileInfo, FileTree
import gui.theme as theme

_STATUS_BG_LIGHT = {
    "new":    ("#DCFCE7", "#15803D"),
    "diff":   ("#FEF9C3", "#854D0E"),
    "skip":   ("#F5F4F0", "#9CA3AF"),
    "synced": ("#F0F9FF", "#0369A1"),
}
_STATUS_BG_DARK = {
    "new":    ("#052E16", "#4ADE80"),
    "diff":   ("#1C1700", "#FCD34D"),
    "skip":   ("#2A2A28", "#8A8A86"),
    "synced": ("#0C1A2E", "#60A5FA"),
}


def _status_bg() -> dict:
    return _STATUS_BG_DARK if theme.is_dark() else _STATUS_BG_LIGHT


class FilePanel(QWidget):
    """Shows a file tree for either local or remote side."""

    def __init__(self, side: str, parent=None) -> None:
        super().__init__(parent)
        self._side = side   # "Local" or "Remote"
        self._files: FileTree = {}
        self._statuses: Dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(30)
        header.setStyleSheet(
            f"background:{theme.surface()}; border-bottom:1px solid {theme.border()};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(6)

        side_label = QLabel(self._side)
        side_label.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{theme.muted()}; background:transparent;"
        )
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setStyleSheet(
            f"font-size:11px; font-family:Consolas,monospace; "
            f"border:1px solid {theme.border()}; border-radius:4px; "
            f"padding:2px 6px; background:{theme.content_bg()};"
        )
        self._path_edit.setFixedHeight(22)

        hl.addWidget(side_label)
        hl.addWidget(self._path_edit, 1)
        root.addWidget(header)

        # Tree
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["Name", "Size", "Modified", "Status"])

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setSortingEnabled(True)
        self._tree.setColumnWidth(0, 240)
        self._tree.setColumnWidth(1, 72)
        self._tree.setColumnWidth(2, 110)
        self._tree.setColumnWidth(3, 60)
        self._tree.header().setStretchLastSection(False)

        root.addWidget(self._tree)

    # ------------------------------------------------------------------
    def set_path(self, path: str) -> None:
        self._path_edit.setText(path)

    def set_files(self, files: FileTree, statuses: Dict[str, str]) -> None:
        self._files = files
        self._statuses = statuses
        self._rebuild()

    def set_statuses(self, statuses: Dict[str, str]) -> None:
        self._statuses = statuses
        self._rebuild()

    def _rebuild(self) -> None:
        self._model.removeRows(0, self._model.rowCount())

        for rel, fi in sorted(self._files.items()):
            status = self._statuses.get(rel, "synced")
            name_item = QStandardItem(rel)
            name_item.setEditable(False)

            size_item = QStandardItem(_fmt_size(fi.size))
            size_item.setEditable(False)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            import datetime as _dt
            mtime_str = _dt.datetime.fromtimestamp(fi.mtime).strftime("%Y-%m-%d %H:%M")
            mtime_item = QStandardItem(mtime_str)
            mtime_item.setEditable(False)
            mtime_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            status_item = QStandardItem(status)
            status_item.setEditable(False)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bg, fg = _status_bg().get(status, _status_bg()["synced"])
            status_item.setForeground(QColor(fg))
            status_item.setBackground(QColor(bg))

            self._model.appendRow([name_item, size_item, mtime_item, status_item])


def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n //= 1024
    return f"{n:.1f} TB"
