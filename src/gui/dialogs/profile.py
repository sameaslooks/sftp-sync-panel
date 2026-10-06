from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QVBoxLayout,
    QWidget,
)

from config import Profile


class ProfileDialog(QDialog):
    def __init__(self, profile: Optional[Profile] = None, parent=None) -> None:
        super().__init__(parent)
        self._editing = profile is not None
        self.setWindowTitle("Edit server" if self._editing else "Add server")
        self.setMinimumWidth(460)
        self._setup_ui()
        if profile:
            self._load(profile)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # Connection
        conn_box = QGroupBox("Connection")
        form = QFormLayout(conn_box)
        form.setSpacing(8)

        self._name = QLineEdit()
        self._name.setPlaceholderText("production")
        form.addRow("Name", self._name)

        host_row = QWidget()
        hl = QHBoxLayout(host_row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)
        self._host = QLineEdit()
        self._host.setPlaceholderText("192.168.1.10")
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(22)
        self._port.setFixedWidth(70)
        hl.addWidget(self._host, 1)
        hl.addWidget(QLabel("Port"))
        hl.addWidget(self._port)
        form.addRow("Host", host_row)

        self._user = QLineEdit()
        self._user.setPlaceholderText("deploy")
        form.addRow("User", self._user)

        root.addWidget(conn_box)

        # Auth
        auth_box = QGroupBox("Authentication")
        af = QFormLayout(auth_box)
        af.setSpacing(8)

        self._auth = QComboBox()
        self._auth.addItems(["SSH agent", "Key file", "Password"])
        self._auth.currentIndexChanged.connect(self._on_auth_changed)
        af.addRow("Method", self._auth)

        key_row = QWidget()
        kl = QHBoxLayout(key_row)
        kl.setContentsMargins(0, 0, 0, 0)
        kl.setSpacing(6)
        self._key_file = QLineEdit()
        self._key_file.setPlaceholderText("~/.ssh/id_ed25519")
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_key)
        kl.addWidget(self._key_file, 1)
        kl.addWidget(browse_btn)
        self._key_row_widget = key_row
        af.addRow("Key file", key_row)

        root.addWidget(auth_box)

        # Paths
        paths_box = QGroupBox("Paths")
        pf = QFormLayout(paths_box)
        pf.setSpacing(8)

        local_row = QWidget()
        ll = QHBoxLayout(local_row)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(6)
        self._local = QLineEdit()
        self._local.setPlaceholderText("D:/projects/myapp")
        browse_local = QPushButton("Browse…")
        browse_local.setFixedWidth(80)
        browse_local.clicked.connect(self._browse_local)
        ll.addWidget(self._local, 1)
        ll.addWidget(browse_local)
        pf.addRow("Local", local_row)

        self._remote = QLineEdit()
        self._remote.setPlaceholderText("/var/www/myapp")
        pf.addRow("Remote", self._remote)

        root.addWidget(paths_box)

        # Options
        opt_box = QGroupBox("Sync options")
        of = QFormLayout(opt_box)
        of.setSpacing(8)

        self._auto_sync = QCheckBox("Enable auto-sync")
        of.addRow("", self._auto_sync)

        self._interval = QSpinBox()
        self._interval.setRange(1, 60)
        self._interval.setValue(2)
        self._interval.setSuffix(" s")
        of.addRow("Debounce interval", self._interval)

        self._compare = QComboBox()
        self._compare.addItems(["mtime (fast)", "md5 (strict)"])
        of.addRow("Compare mode", self._compare)

        root.addWidget(opt_box)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._on_auth_changed(0)

    # ------------------------------------------------------------------
    def _on_auth_changed(self, index: int) -> None:
        self._key_row_widget.setVisible(index == 1)   # Key file only

    def _browse_key(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select key file", "", "All files (*)")
        if path:
            self._key_file.setText(path)

    def _browse_local(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select local folder")
        if path:
            self._local.setText(path)

    def _load(self, p: Profile) -> None:
        self._name.setText(p.name)
        self._host.setText(p.host)
        self._port.setValue(p.port)
        self._user.setText(p.user)
        auth_map = {"agent": 0, "key_file": 1, "password": 2}
        self._auth.setCurrentIndex(auth_map.get(p.auth, 0))
        self._key_file.setText(p.key_file)
        self._local.setText(p.local_path)
        self._remote.setText(p.remote_path)
        self._auto_sync.setChecked(p.auto_sync)
        self._interval.setValue(p.auto_sync_interval)
        self._compare.setCurrentIndex(0 if p.compare_mode == "mtime" else 1)

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            self._name.setFocus()
            return
        if not self._host.text().strip():
            self._host.setFocus()
            return
        self.accept()

    # ------------------------------------------------------------------
    def get_profile(self) -> Profile:
        auth_map = {0: "agent", 1: "key_file", 2: "password"}
        return Profile(
            name=self._name.text().strip(),
            host=self._host.text().strip(),
            port=self._port.value(),
            user=self._user.text().strip(),
            auth=auth_map[self._auth.currentIndex()],
            key_file=self._key_file.text().strip(),
            local_path=self._local.text().strip(),
            remote_path=self._remote.text().strip(),
            exclusions=[],
            auto_sync=self._auto_sync.isChecked(),
            auto_sync_interval=self._interval.value(),
            compare_mode="mtime" if self._compare.currentIndex() == 0 else "md5",
        )
