from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
import gui.theme as theme

_COLORS_LIGHT = {
    "info":    "#1A1A18",
    "success": "#15803D",
    "warning": "#B45309",
    "error":   "#DC2626",
}

_COLORS_DARK = {
    "info":    "#E8E7E4",
    "success": "#4ADE80",
    "warning": "#FCD34D",
    "error":   "#F87171",
}


def _colors() -> dict:
    return _COLORS_DARK if theme.is_dark() else _COLORS_LIGHT


class LogPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("logPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(28)
        header.setStyleSheet(
            f"background:{theme.surface()}; border-bottom:1px solid {theme.border()};"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)
        title = QLabel("Log")
        title.setStyleSheet(
            f"font-size:11px;font-weight:600;color:{theme.muted()};background:transparent;"
        )
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(20)
        clear_btn.setStyleSheet(
            f"font-size:11px; border:none; color:{theme.muted()}; background:transparent; padding:0 4px;"
        )
        clear_btn.clicked.connect(self.clear)
        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(clear_btn)
        root.addWidget(header)

        # Log area
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        root.addWidget(self._text, 1)

        # Progress
        progress_bar_widget = QWidget()
        progress_bar_widget.setFixedHeight(20)
        progress_bar_widget.setStyleSheet(
            f"background:{theme.bg()}; border-top:1px solid {theme.border()};"
        )
        pl = QHBoxLayout(progress_bar_widget)
        pl.setContentsMargins(8, 4, 8, 4)
        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet(
            f"font-size:10px; color:{theme.muted()}; background:transparent;"
        )
        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        pl.addWidget(self._progress_label)
        pl.addWidget(self._progress_bar, 1)
        root.addWidget(progress_bar_widget)

    # ------------------------------------------------------------------
    def append(self, message: str, level: str = "info") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        colors = _colors()
        color = colors.get(level, colors["info"])

        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        fmt_ts = QTextCharFormat()
        fmt_ts.setForeground(QColor("#4A4A48" if theme.is_dark() else "#B5B4B0"))

        fmt_msg = QTextCharFormat()
        fmt_msg.setForeground(QColor(color))

        if not self._text.toPlainText():
            pass
        else:
            cursor.insertText("\n")

        cursor.setCharFormat(fmt_ts)
        cursor.insertText(f"{ts}  ")
        cursor.setCharFormat(fmt_msg)
        cursor.insertText(message)

        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()

    def set_progress(self, current: int, total: int, message: str = "") -> None:
        if total > 0:
            pct = int(current / total * 100)
            self._progress_bar.setVisible(True)
            self._progress_bar.setValue(pct)
            self._progress_label.setText(
                message or f"{current} / {total}"
            )
        else:
            self._progress_bar.setVisible(False)
            self._progress_label.setText("")

    def clear_progress(self) -> None:
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_label.setText("")

    def clear(self) -> None:
        self._text.clear()
        self.clear_progress()
