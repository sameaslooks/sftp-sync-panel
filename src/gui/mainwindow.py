from __future__ import annotations

from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap

from config import Profile, load_profiles, save_profiles
from gui.serverpanel import ServerPanel
from gui.synctab import SyncTab
import gui.theme as theme


def _tab_icon(color: str) -> QIcon:
    px = QPixmap(10, 10)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(color)))
    p.setPen(QColor(0, 0, 0, 0))
    p.drawEllipse(1, 1, 8, 8)
    p.end()
    return QIcon(px)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SFTP Sync Panel")
        self.setMinimumSize(900, 580)
        self.resize(1240, 760)

        self._profiles = load_profiles()
        self._tabs: Dict[str, SyncTab] = {}

        self._setup_ui()
        self._setup_statusbar()

    # ── UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)

        self._server_panel = ServerPanel(self._profiles)
        self._server_panel.setMinimumWidth(140)
        self._server_panel.setMaximumWidth(300)
        self._server_panel.profile_connect_requested.connect(self._open_tab)
        self._server_panel.profile_added.connect(self._on_profile_added)
        self._server_panel.profile_edited.connect(self._on_profile_edited)
        self._server_panel.profile_deleted.connect(self._on_profile_deleted)

        # Stack: 0 = empty state, 1 = tab widget
        self._stack = QStackedWidget()

        self._empty_state = self._build_empty_state()
        self._stack.addWidget(self._empty_state)

        self._tabs_widget = QTabWidget()
        self._tabs_widget.setTabsClosable(True)
        self._tabs_widget.tabCloseRequested.connect(self._close_tab)
        self._tabs_widget.setStyleSheet(
            "QTabWidget::pane { border:none; }"
        )
        self._stack.addWidget(self._tabs_widget)

        splitter.addWidget(self._server_panel)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([170, 1070])

        layout.addWidget(splitter)

    def _build_empty_state(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        title = QLabel("sftp-sync-panel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        muted = theme.muted()
        title.setStyleSheet(
            f"font-size:22px; font-weight:500; color:{muted}; background:transparent;"
        )

        hint = QLabel("Add a server in the left panel,\nthen double-click to connect.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(
            f"font-size:13px; color:{muted}; background:transparent; opacity:0.6;"
        )

        layout.addWidget(title)
        layout.addWidget(hint)
        return widget

    def _show_empty_state(self, show: bool) -> None:
        self._stack.setCurrentIndex(0 if show else 1)

    def _setup_statusbar(self) -> None:
        sb = self.statusBar()
        sb.setStyleSheet(
            f"QStatusBar {{ background:{theme.surface()}; border-top:1px solid {theme.border()}; "
            f"font-size:11px; color:{theme.muted()}; }}"
            "QStatusBar::item { border:none; }"
        )
        self._sb_connections = QLabel("No active connections")
        self._sb_connections.setStyleSheet("margin:0 8px;")
        sb.addWidget(self._sb_connections)

        self._sb_right = QLabel()
        self._sb_right.setStyleSheet("margin:0 8px;")
        sb.addPermanentWidget(self._sb_right)

        self._update_statusbar()

    def _update_statusbar(self) -> None:
        active = [n for n, t in self._tabs.items() if t.is_connected()]
        idle   = [n for n, t in self._tabs.items() if not t.is_connected()]

        parts = []
        if active:
            parts.append(f"{len(active)} active")
        if idle:
            parts.append(f"{len(idle)} idle")
        total_profiles = len(self._profiles)
        parts.append(f"{total_profiles} profile(s) configured")

        self._sb_connections.setText("  ·  ".join(parts) if parts else "No active connections")

    # ── Tab management ───────────────────────────────────────────────────

    def _open_tab(self, profile: Profile) -> None:
        if profile.name in self._tabs:
            for i in range(self._tabs_widget.count()):
                if self._tabs_widget.tabText(i) == profile.name:
                    self._tabs_widget.setCurrentIndex(i)
            return

        tab = SyncTab(profile)
        tab.connection_state_changed.connect(self._on_tab_state_changed)
        tab.disconnect_requested.connect(lambda n=profile.name: self._close_tab_by_name(n))
        self._tabs[profile.name] = tab

        idx = self._tabs_widget.addTab(tab, profile.name)
        self._tabs_widget.setTabIcon(idx, _tab_icon("#F59E0B"))
        self._tabs_widget.setCurrentIndex(idx)
        self._server_panel.set_status(profile.name, "connecting")
        self._show_empty_state(False)

        tab.start_connect()
        self._update_statusbar()

    def _close_tab_by_name(self, name: str) -> None:
        for i in range(self._tabs_widget.count()):
            if self._tabs_widget.tabText(i) == name:
                self._close_tab(i)
                return

    def _close_tab(self, index: int) -> None:
        name = self._tabs_widget.tabText(index)
        tab = self._tabs.pop(name, None)
        if tab:
            tab.disconnect()
        self._tabs_widget.removeTab(index)
        self._server_panel.set_status(name, "disconnected")
        if self._tabs_widget.count() == 0:
            self._show_empty_state(True)
        self._update_statusbar()

    def _on_tab_state_changed(self) -> None:
        for name, tab in self._tabs.items():
            connected = tab.is_connected()
            self._server_panel.set_status(name, "connected" if connected else "disconnected")
            # Update tab icon color
            for i in range(self._tabs_widget.count()):
                if self._tabs_widget.tabText(i) == name:
                    color = "#22C55E" if connected else "#9CA3AF"
                    self._tabs_widget.setTabIcon(i, _tab_icon(color))
                    break
        self._update_statusbar()

    # ── Profile management ───────────────────────────────────────────────

    def _on_profile_added(self, profile: Profile) -> None:
        self._profiles.append(profile)
        save_profiles(self._profiles)
        self._update_statusbar()

    def _on_profile_edited(self, old_name: str, profile: Profile) -> None:
        for i, p in enumerate(self._profiles):
            if p.name == old_name:
                self._profiles[i] = profile
                break
        save_profiles(self._profiles)

    def _on_profile_deleted(self, name: str) -> None:
        self._profiles[:] = [p for p in self._profiles if p.name != name]
        save_profiles(self._profiles)
        self._update_statusbar()

    # ── Lifecycle ────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        for tab in self._tabs.values():
            tab.disconnect()
        save_profiles(self._profiles)
        super().closeEvent(event)
