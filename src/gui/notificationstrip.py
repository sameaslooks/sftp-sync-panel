from __future__ import annotations

from typing import Callable, Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class _Chip(QWidget):
    """A single non-blocking delete prompt."""

    def __init__(
        self,
        path: str,
        on_delete: Callable[[], None],
        on_keep: Callable[[], None],
    ) -> None:
        super().__init__()
        self.setStyleSheet(
            "background:#FFFBEB; border:1px solid #FDE68A; border-radius:6px; padding:2px 6px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(6)

        label = QLabel(f"<b>{path}</b> deleted locally — remove on remote?")
        label.setStyleSheet("font-size:12px; color:#92400E; background:transparent; border:none;")
        layout.addWidget(label, 1)

        del_btn = QPushButton("Delete remote")
        del_btn.setProperty("danger", "true")
        del_btn.setFixedHeight(22)
        del_btn.setStyleSheet(
            "font-size:11px; border:1px solid #FCA5A5; border-radius:4px; "
            "color:#DC2626; background:transparent; padding:0 8px;"
        )
        del_btn.clicked.connect(on_delete)
        layout.addWidget(del_btn)

        keep_btn = QPushButton("Keep")
        keep_btn.setFixedHeight(22)
        keep_btn.setStyleSheet(
            "font-size:11px; border:1px solid #D1D0CC; border-radius:4px; "
            "color:#6B6B66; background:transparent; padding:0 8px;"
        )
        keep_btn.clicked.connect(on_keep)
        layout.addWidget(keep_btn)


class NotificationStrip(QWidget):
    """
    Horizontal scrollable strip of non-blocking delete prompts.
    Hidden when empty.

    Emits:
        delete_requested(path)  – user clicked "Delete remote"
        dismissed(path)         – user clicked "Keep" or chip was removed
    """

    delete_requested = pyqtSignal(str)
    dismissed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("notifStrip")
        self.setVisible(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(42)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: #FFFBEB; }"
        )

        self._inner = QWidget()
        self._inner.setStyleSheet("background: #FFFBEB;")
        self._layout = QHBoxLayout(self._inner)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(6)
        self._layout.addStretch()

        scroll.setWidget(self._inner)
        outer.addWidget(scroll)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #FDE68A;")
        outer.addWidget(sep)

        self._chips: Dict[str, _Chip] = {}

    # ------------------------------------------------------------------
    def add(self, path: str) -> None:
        if path in self._chips:
            return

        def on_delete() -> None:
            self._remove_chip(path)
            self.delete_requested.emit(path)

        def on_keep() -> None:
            self._remove_chip(path)
            self.dismissed.emit(path)

        chip = _Chip(path, on_delete, on_keep)
        self._chips[path] = chip
        # Insert before the trailing stretch
        self._layout.insertWidget(self._layout.count() - 1, chip)
        self.setVisible(True)

    def remove(self, path: str) -> None:
        self._remove_chip(path)

    def _remove_chip(self, path: str) -> None:
        chip = self._chips.pop(path, None)
        if chip:
            self._layout.removeWidget(chip)
            chip.deleteLater()
        if not self._chips:
            self.setVisible(False)
