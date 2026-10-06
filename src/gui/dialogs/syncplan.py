from __future__ import annotations

from typing import List, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from engine.differ import OpType, SyncOp


_OP_LABEL = {
    OpType.ADD:    ("Upload (new)",  "#15803D", "#DCFCE7"),
    OpType.UPDATE: ("Upload (diff)", "#854D0E", "#FEF9C3"),
    OpType.DELETE: ("Delete remote", "#DC2626", "#FEF2F2"),
}


class SyncPlanDialog(QDialog):
    """
    Shows the computed sync plan before executing.
    Returns (confirmed: bool, ops: List[SyncOp], dry_run: bool).
    """

    def __init__(self, ops: List[SyncOp], parent=None) -> None:
        super().__init__(parent)
        self._ops = ops
        self.setWindowTitle("Sync plan")
        self.setMinimumSize(560, 420)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)

        # Summary
        adds    = sum(1 for o in self._ops if o.op == OpType.ADD)
        updates = sum(1 for o in self._ops if o.op == OpType.UPDATE)
        deletes = sum(1 for o in self._ops if o.op == OpType.DELETE)

        summary = QLabel(
            f"<b>{len(self._ops)} operations</b> — "
            f"<span style='color:#15803D'>{adds} new</span>  "
            f"<span style='color:#854D0E'>{updates} changed</span>  "
            f"<span style='color:#DC2626'>{deletes} to delete</span>"
        )
        summary.setStyleSheet("font-size:13px; padding:4px 0;")
        root.addWidget(summary)

        # Tree
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Operation", "Path"])

        for op in self._ops:
            label, fg, bg = _OP_LABEL[op.op]
            op_item = QStandardItem(label)
            op_item.setEditable(False)
            op_item.setForeground(QColor(fg))
            op_item.setBackground(QColor(bg))

            path_item = QStandardItem(op.path)
            path_item.setEditable(False)

            model.appendRow([op_item, path_item])

        tree = QTreeView()
        tree.setModel(model)
        tree.setRootIsDecorated(False)
        tree.setColumnWidth(0, 130)
        tree.header().setStretchLastSection(True)
        tree.setAlternatingRowColors(True)
        root.addWidget(tree, 1)

        # Mirror delete section (only shown if there are deletes)
        if deletes > 0:
            del_frame_label = QLabel(
                f"⚠  {deletes} file(s) will be moved to remote trash (.synctool-trash/)."
            )
            del_frame_label.setStyleSheet(
                "background:#FEF2F2; border:1px solid #FCA5A5; border-radius:6px; "
                "padding:6px 10px; color:#991B1B; font-size:12px;"
            )
            del_frame_label.setWordWrap(True)
            root.addWidget(del_frame_label)

        # Options
        self._dry_run_cb = QCheckBox("Dry run (show plan, do not transfer)")
        root.addWidget(self._dry_run_cb)

        # Buttons
        btn_box = QDialogButtonBox()
        cancel_btn = btn_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        sync_btn = btn_box.addButton("Sync now", QDialogButtonBox.ButtonRole.AcceptRole)
        sync_btn.setProperty("accent", "true")
        sync_btn.style().unpolish(sync_btn)
        sync_btn.style().polish(sync_btn)

        btn_box.rejected.connect(self.reject)
        btn_box.accepted.connect(self._confirm)
        root.addWidget(btn_box)

    def _confirm(self) -> None:
        # Extra confirm if there are deletions
        deletes = [o for o in self._ops if o.op == OpType.DELETE]
        if deletes and not self._dry_run_cb.isChecked():
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("Confirm remote deletions")
            msg.setText(
                f"You are about to move <b>{len(deletes)} file(s)</b> "
                f"to remote trash.<br><br>"
                + "<br>".join(f"• {o.path}" for o in deletes[:10])
                + ("<br>…" if len(deletes) > 10 else "")
            )
            msg.setIcon(QMessageBox.Icon.Warning)
            del_btn = msg.addButton(
                f"Move {len(deletes)} file(s) to trash",
                QMessageBox.ButtonRole.DestructiveRole,
            )
            msg.addButton(QMessageBox.StandardButton.Cancel)
            msg.exec()
            if msg.clickedButton() != del_btn:
                return
        self.accept()

    # ------------------------------------------------------------------
    def result_ops(self) -> Tuple[List[SyncOp], bool]:
        """Returns (ops, dry_run)."""
        return self._ops, self._dry_run_cb.isChecked()
