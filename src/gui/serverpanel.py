from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import Profile
from engine.connection import get_agent_keys
import gui.theme as theme


_STATUS_COLOR = {
    "connected":    "#22C55E",
    "connecting":   "#F59E0B",
    "disconnected": "#9CA3AF",
    "error":        "#EF4444",
}


def _dot_icon(color: str, size: int = 16) -> QIcon:
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(color)))
    p.setPen(Qt.PenStyle.NoPen)
    d = 8
    margin = (size - d) // 2
    p.drawEllipse(margin, margin, d, d)
    p.end()
    return QIcon(px)


class _ServerItem(QListWidgetItem):
    def __init__(self, profile: Profile) -> None:
        super().__init__()
        self.profile = profile
        self._status = "disconnected"
        self._refresh()

    def _refresh(self) -> None:
        color = _STATUS_COLOR.get(self._status, _STATUS_COLOR["disconnected"])
        self.setIcon(_dot_icon(color))
        self.setText(f"{self.profile.name}\n{self.profile.user}@{self.profile.host}")
        self.setForeground(QColor(theme.text()))

    def set_status(self, status: str) -> None:
        self._status = status
        self._refresh()


class ServerPanel(QWidget):
    """Left sidebar showing all configured server profiles."""

    profile_connect_requested = pyqtSignal(object)
    profile_added             = pyqtSignal(object)
    profile_edited            = pyqtSignal(str, object)
    profile_deleted           = pyqtSignal(str)

    def __init__(self, profiles: List[Profile], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("serverPanel")
        self._profiles = profiles
        self._items: dict[str, _ServerItem] = {}
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(32)
        header.setStyleSheet(
            f"background:{theme.surface()}; border-bottom:1px solid {theme.border()};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 0, 10, 0)
        title = QLabel("Servers")
        title.setStyleSheet(
            f"font-size:11px;font-weight:600;color:{theme.muted()};background:transparent;"
        )
        hl.addWidget(title)
        hl.addStretch()
        root.addWidget(header)

        self._list = QListWidget()
        self._list.setIconSize(QSize(14, 14))
        self._list.setSpacing(0)
        sel_bg = "#1E3A5F" if theme.is_dark() else "#EFF6FF"
        hover_bg = "#2E2E2C" if theme.is_dark() else "#E8E7E3"
        self._list.setStyleSheet(
            f"QListWidget {{ background:{theme.surface()}; border:none; outline:none; }}"
            f"QListWidget::item {{ padding:6px 8px; border-bottom:1px solid {theme.border()}; }}"
            f"QListWidget::item:selected {{ background:{sel_bg}; }}"
            f"QListWidget::item:hover:!selected {{ background:{hover_bg}; }}"
        )
        self._list.itemDoubleClicked.connect(self._on_double_click)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        root.addWidget(self._list, 1)

        add_btn = QPushButton("+ Add server")
        add_btn.setStyleSheet(
            f"border:none; border-top:1px solid {theme.border()}; "
            f"background:{theme.surface()}; "
            "color:#3B82F6; font-size:12px; padding:8px 10px; text-align:left;"
        )
        add_btn.clicked.connect(self._add_profile)
        root.addWidget(add_btn)

        # SSH agent indicator
        self._agent_widget = QWidget()
        self._agent_widget.setFixedHeight(40)
        self._agent_widget.setStyleSheet(
            f"background:{theme.surface()}; border-top:1px solid {theme.border()};"
        )
        al = QHBoxLayout(self._agent_widget)
        al.setContentsMargins(10, 4, 10, 4)
        al.setSpacing(8)
        self._agent_dot = QLabel()
        self._agent_dot.setFixedSize(8, 8)
        self._agent_label = QLabel()
        self._agent_label.setStyleSheet(
            f"font-size:10px; color:{theme.muted()}; background:transparent;"
        )
        al.addWidget(self._agent_dot)
        al.addWidget(self._agent_label, 1)
        root.addWidget(self._agent_widget)
        self._agent_widget.mousePressEvent = lambda e: self._show_agent_info()

        self._refresh_agent()

    def _populate(self) -> None:
        for p in self._profiles:
            item = _ServerItem(p)
            self._list.addItem(item)
        self._sync_items()

    def _sync_items(self) -> None:
        """Rebuild _items from the actual list widget contents."""
        self._items.clear()
        for i in range(self._list.count()):
            it = self._list.item(i)
            if isinstance(it, _ServerItem):
                self._items[it.profile.name] = it

    def _refresh_agent(self) -> None:
        keys = get_agent_keys()
        if keys:
            types = ", ".join(k["type"] for k in keys[:3])
            self._agent_label.setText(f"SSH agent: {len(keys)} key(s)")
            self._agent_label.setStyleSheet(
                "font-size:10px; color:#15803D; background:transparent;"
            )
            self._agent_dot.setStyleSheet(
                "background:#22C55E; border-radius:4px;"
            )
        else:
            self._agent_label.setText("SSH agent: no keys")
            self._agent_label.setStyleSheet(
                "font-size:10px; color:#B45309; background:transparent;"
            )
            self._agent_dot.setStyleSheet(
                "background:#F59E0B; border-radius:4px;"
            )

    # ------------------------------------------------------------------
    def set_status(self, profile_name: str, status: str) -> None:
        item = self._items.get(profile_name)
        if item:
            item.set_status(status)

    # ------------------------------------------------------------------
    def _on_double_click(self, item: QListWidgetItem) -> None:
        if isinstance(item, _ServerItem):
            self.profile_connect_requested.emit(item.profile)

    def _on_context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if not isinstance(item, _ServerItem):
            return
        menu = QMenu(self)
        menu.addAction("Connect").triggered.connect(
            lambda: self.profile_connect_requested.emit(item.profile)
        )
        menu.addAction("Edit…").triggered.connect(lambda: self._edit_profile(item))
        menu.addSeparator()
        menu.addAction("Delete").triggered.connect(lambda: self._delete_profile(item))
        menu.exec(self._list.mapToGlobal(pos))

    def _add_profile(self) -> None:
        from gui.dialogs.profile import ProfileDialog
        dlg = ProfileDialog(parent=self)
        if dlg.exec():
            p = dlg.get_profile()
            item = _ServerItem(p)
            self._list.addItem(item)
            self._sync_items()
            self.profile_added.emit(p)

    def _edit_profile(self, item: _ServerItem) -> None:
        from gui.dialogs.profile import ProfileDialog
        dlg = ProfileDialog(profile=item.profile, parent=self)
        if dlg.exec():
            old_name = item.profile.name
            new_profile = dlg.get_profile()
            new_profile.exclusions = item.profile.exclusions
            item.profile = new_profile
            item._refresh()
            self._sync_items()
            self.profile_edited.emit(old_name, new_profile)

    def _delete_profile(self, item: _ServerItem) -> None:
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Delete profile",
            f"Delete profile «{item.profile.name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            name = item.profile.name
            self._list.takeItem(self._list.row(item))
            self._sync_items()
            self.profile_deleted.emit(name)

    def _show_agent_info(self) -> None:
        from gui.dialogs.agent import AgentInfoDialog
        AgentInfoDialog(parent=self).exec()
        self._refresh_agent()
