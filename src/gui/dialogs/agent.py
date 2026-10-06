from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTreeView,
    QVBoxLayout,
)

from engine.connection import get_agent_keys


class AgentInfoDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SSH agent keys")
        self.setMinimumSize(520, 280)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)

        keys = get_agent_keys()

        if not keys:
            label = QLabel(
                "No keys loaded in SSH agent.\n\n"
                "Enable the OpenSSH agent service and add a key:\n\n"
                "    Set-Service -Name ssh-agent -StartupType Automatic\n"
                "    Start-Service ssh-agent\n"
                "    ssh-add ~/.ssh/id_ed25519"
            )
            label.setStyleSheet(
                "color:#6B6B66; font-family:Consolas,monospace; font-size:12px;"
            )
            root.addWidget(label)
        else:
            label = QLabel(f"{len(keys)} key(s) loaded")
            label.setStyleSheet("font-size:13px;")
            root.addWidget(label)

            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["Type", "Fingerprint", "Comment"])

            for k in keys:
                row = [
                    QStandardItem(k.get("type", "")),
                    QStandardItem(k.get("fingerprint", "")),
                    QStandardItem(k.get("comment", "")),
                ]
                for item in row:
                    item.setEditable(False)
                model.appendRow(row)

            tree = QTreeView()
            tree.setModel(model)
            tree.setRootIsDecorated(False)
            tree.setAlternatingRowColors(True)
            tree.setColumnWidth(0, 90)
            tree.setColumnWidth(1, 280)
            tree.header().setStretchLastSection(True)
            root.addWidget(tree, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        root.addWidget(buttons)
