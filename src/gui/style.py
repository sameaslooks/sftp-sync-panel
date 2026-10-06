_LIGHT = """
QMainWindow, QDialog {
    background: #F9F8F6;
}
QWidget {
    font-family: "Segoe UI", "SF Pro Text", sans-serif;
    font-size: 13px;
    color: #1A1A18;
    background: #F9F8F6;
}
QTreeView, QListWidget, QTextEdit, QLineEdit,
QSpinBox, QComboBox, QAbstractItemView {
    background: #FFFFFF;
    color: #1A1A18;
}
QSplitter::handle { background: #E4E3DF; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }
QTabWidget::pane  { border: none; }
QTabBar            { background: #F0EFE9; }
QTabBar::tab {
    background: #F0EFE9; border: none;
    border-right: 1px solid #E4E3DF;
    padding: 7px 16px 7px 12px;
    font-size: 12px; color: #6B6B66;
}
QTabBar::tab:selected {
    background: #F9F8F6; color: #1A1A18;
    border-top: 2px solid #3B82F6;
}
QTabBar::tab:hover:!selected { background: #E8E7E3; color: #1A1A18; }
QTreeView, QListWidget {
    border: none; alternate-background-color: #FAFAF8; outline: none;
}
QTreeView::item, QListWidget::item { height: 24px; padding-left: 4px; }
QTreeView::item:selected, QListWidget::item:selected {
    background: #EFF6FF; color: #1A1A18;
}
QTreeView::item:hover:!selected, QListWidget::item:hover:!selected { background: #F5F4F0; }
QHeaderView::section {
    background: #F0EFE9; border: none;
    border-right: 1px solid #E4E3DF; border-bottom: 1px solid #E4E3DF;
    padding: 4px 8px; font-size: 11px; color: #6B6B66; font-weight: 600;
}
QPushButton {
    background: transparent; border: 1px solid #D1D0CC;
    border-radius: 6px; padding: 4px 12px;
    font-size: 12px; color: #1A1A18; min-height: 26px;
}
QPushButton:hover  { background: #F0EFE9; border-color: #B5B4B0; }
QPushButton:pressed { background: #E8E7E3; }
QPushButton:disabled { color: #B5B4B0; border-color: #E4E3DF; }
QPushButton[accent="true"] { border-color: #93C5FD; color: #1D4ED8; }
QPushButton[accent="true"]:hover { background: #EFF6FF; }
QPushButton[danger="true"] { border-color: #FCA5A5; color: #DC2626; }
QPushButton[danger="true"]:hover { background: #FEF2F2; }
QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #D1D0CC; border-radius: 6px;
    padding: 5px 8px; background: #FFFFFF; color: #1A1A18; min-height: 28px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #3B82F6; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    border: 1px solid #D1D0CC; background: #FFFFFF;
    selection-background-color: #EFF6FF;
}
QCheckBox { spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #D1D0CC;
    border-radius: 4px; background: #FFFFFF;
}
QCheckBox::indicator:checked { background: #3B82F6; border-color: #3B82F6; }
QGroupBox {
    border: 1px solid #E4E3DF; border-radius: 8px;
    margin-top: 10px; padding-top: 6px;
    font-size: 11px; font-weight: 600; color: #6B6B66;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; background: #F9F8F6; }
QProgressBar {
    border: none; background: #E4E3DF; border-radius: 3px;
    max-height: 4px; font-size: 0px;
}
QProgressBar::chunk { background: #3B82F6; border-radius: 3px; }
QScrollBar:vertical   { border: none; background: transparent; width: 8px; }
QScrollBar:horizontal { border: none; background: transparent; height: 8px; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #D1D0CC; border-radius: 4px; min-height: 30px; min-width: 30px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #B5B4B0; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QStatusBar {
    background: #F0EFE9; border-top: 1px solid #E4E3DF;
    color: #6B6B66; font-size: 11px;
}
QStatusBar::item { border: none; }
#toolbar { background: #F9F8F6; border-bottom: 1px solid #E4E3DF; }
#serverPanel { background: #F0EFE9; }
#notifStrip { background: #FFFBEB; border-bottom: 1px solid #FDE68A; }
#logPanel QTextEdit { border: none; font-family: "Consolas","Cascadia Mono",monospace; font-size: 12px; }
#exclusionsPanel { background: #F9F8F6; border-right: 1px solid #E4E3DF; }
"""

_DARK = """
QMainWindow, QDialog { background: #1A1A18; }
QWidget {
    font-family: "Segoe UI", "SF Pro Text", sans-serif;
    font-size: 13px; color: #E8E7E4; background: #1A1A18;
}
QTreeView, QListWidget, QTextEdit, QLineEdit,
QSpinBox, QComboBox, QAbstractItemView {
    background: #252523; color: #E8E7E4;
}
QSplitter::handle { background: #333331; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }
QTabWidget::pane  { border: none; }
QTabBar            { background: #222220; }
QTabBar::tab {
    background: #222220; border: none;
    border-right: 1px solid #333331;
    padding: 7px 16px 7px 12px; font-size: 12px; color: #8A8A86;
}
QTabBar::tab:selected {
    background: #1A1A18; color: #E8E7E4;
    border-top: 2px solid #60A5FA;
}
QTabBar::tab:hover:!selected { background: #2A2A28; color: #E8E7E4; }
QTreeView, QListWidget {
    border: none; alternate-background-color: #2A2A28; outline: none;
}
QTreeView::item, QListWidget::item { height: 24px; padding-left: 4px; }
QTreeView::item:selected, QListWidget::item:selected {
    background: #1E3A5F; color: #E8E7E4;
}
QTreeView::item:hover:!selected, QListWidget::item:hover:!selected { background: #2E2E2C; }
QHeaderView::section {
    background: #222220; border: none;
    border-right: 1px solid #333331; border-bottom: 1px solid #333331;
    padding: 4px 8px; font-size: 11px; color: #8A8A86; font-weight: 600;
}
QPushButton {
    background: transparent; border: 1px solid #3A3A38;
    border-radius: 6px; padding: 4px 12px;
    font-size: 12px; color: #E8E7E4; min-height: 26px;
}
QPushButton:hover  { background: #2A2A28; border-color: #4A4A48; }
QPushButton:pressed { background: #333331; }
QPushButton:disabled { color: #4A4A48; border-color: #2A2A28; }
QPushButton[accent="true"] { border-color: #1D4ED8; color: #60A5FA; }
QPushButton[accent="true"]:hover { background: #1E3A5F; }
QPushButton[danger="true"] { border-color: #7F1D1D; color: #F87171; }
QPushButton[danger="true"]:hover { background: #2D1010; }
QLineEdit, QSpinBox, QComboBox {
    border: 1px solid #3A3A38; border-radius: 6px;
    padding: 5px 8px; background: #252523; color: #E8E7E4; min-height: 28px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #60A5FA; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    border: 1px solid #3A3A38; background: #252523;
    selection-background-color: #1E3A5F;
}
QCheckBox { spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #3A3A38;
    border-radius: 4px; background: #252523;
}
QCheckBox::indicator:checked { background: #3B82F6; border-color: #3B82F6; }
QGroupBox {
    border: 1px solid #333331; border-radius: 8px;
    margin-top: 10px; padding-top: 6px;
    font-size: 11px; font-weight: 600; color: #8A8A86;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; background: #1A1A18; }
QProgressBar {
    border: none; background: #333331; border-radius: 3px;
    max-height: 4px; font-size: 0px;
}
QProgressBar::chunk { background: #3B82F6; border-radius: 3px; }
QScrollBar:vertical   { border: none; background: transparent; width: 8px; }
QScrollBar:horizontal { border: none; background: transparent; height: 8px; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #3A3A38; border-radius: 4px; min-height: 30px; min-width: 30px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #4A4A48; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QStatusBar {
    background: #222220; border-top: 1px solid #333331;
    color: #8A8A86; font-size: 11px;
}
QStatusBar::item { border: none; }
#toolbar { background: #1A1A18; border-bottom: 1px solid #333331; }
#serverPanel { background: #222220; }
#notifStrip { background: #2D2310; border-bottom: 1px solid #78350F; }
#logPanel QTextEdit { border: none; font-family: "Consolas","Cascadia Mono",monospace; font-size: 12px; }
#exclusionsPanel { background: #1A1A18; border-right: 1px solid #333331; }
"""


def get_qss(dark: bool = False) -> str:
    return _DARK if dark else _LIGHT


# Keep QSS as default light for backward compat
QSS = _LIGHT
