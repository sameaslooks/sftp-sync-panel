from __future__ import annotations

import os
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class ExclusionsDialog(QDialog):
    def __init__(self, exclusions: List[str], local_path: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Exclusion rules")
        self.setMinimumSize(420, 380)
        self._exclusions = list(exclusions)
        self._local_path = local_path
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(8)

        hint = QLabel(
            "Glob patterns — one per line. Matches file names and path segments.<br>"
            "Examples: <tt>node_modules/</tt> &nbsp; <tt>.env*</tt> &nbsp;"
            " <tt>*.log</tt> &nbsp; <tt>dist/</tt>"
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setStyleSheet("color:#6B6B66; font-size:12px;")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        for exc in self._exclusions:
            self._list.addItem(exc)
        root.addWidget(self._list, 1)

        add_row = QHBoxLayout()
        self._new_edit = QLineEdit()
        self._new_edit.setPlaceholderText("node_modules/")
        self._new_edit.returnPressed.connect(self._add)
        add_btn = QPushButton("Add")
        add_btn.setFixedWidth(60)
        add_btn.clicked.connect(self._add)
        add_row.addWidget(self._new_edit, 1)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

        actions_row = QHBoxLayout()
        gitignore_btn = QPushButton("Load .gitignore…")
        gitignore_btn.clicked.connect(self._load_gitignore)

        del_btn = QPushButton("Remove selected")
        del_btn.setProperty("danger", "true")
        del_btn.clicked.connect(self._remove)

        actions_row.addWidget(gitignore_btn)
        actions_row.addStretch()
        actions_row.addWidget(del_btn)
        root.addLayout(actions_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _add(self) -> None:
        text = self._new_edit.text().strip()
        if text:
            self._list.addItem(text)
            self._new_edit.clear()

    def _remove(self) -> None:
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def _load_gitignore(self) -> None:
        start_dir = self._local_path or ""
        # Suggest .gitignore in local_path if it exists
        suggested = os.path.join(start_dir, ".gitignore") if start_dir else ""
        if suggested and os.path.isfile(suggested):
            path = suggested
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select .gitignore",
                start_dir,
                "gitignore files (.gitignore *.gitignore);;All files (*)",
            )
        if not path:
            return

        existing = set(self.get_exclusions())
        added = 0
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#") or line.startswith("!"):
                        continue
                    if line not in existing:
                        self._list.addItem(line)
                        existing.add(line)
                        added += 1
        except OSError as e:
            QMessageBox.warning(self, "Error", f"Could not read file:\n{e}")
            return

        QMessageBox.information(
            self,
            "Loaded",
            f"Added {added} pattern(s) from .gitignore\n({path})" if added
            else "No new patterns found (all already listed).",
        )

    def get_exclusions(self) -> List[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]
