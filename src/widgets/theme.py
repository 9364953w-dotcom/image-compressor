"""
主题系统：统一颜色 token 和全局 QSS。
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ThemeTokens:
    name: str
    bg: str
    surface: str
    surface_alt: str
    border: str
    text_primary: str
    text_secondary: str
    accent: str
    accent_hover: str
    success: str
    warning: str
    error: str


THEMES = {
    "HumanityDark": ThemeTokens(
        name="HumanityDark",
        bg="#1f1f1f",
        surface="#2a2a2a",
        surface_alt="#333333",
        border="#4a4a4a",
        text_primary="#f2f2f2",
        text_secondary="#b5b5b5",
        accent="#f39c12",
        accent_hover="#ffad33",
        success="#27ae60",
        warning="#f1c40f",
        error="#e74c3c",
    ),
    "CosmicDusk": ThemeTokens(
        name="CosmicDusk",
        bg="#171a26",
        surface="#20253a",
        surface_alt="#2b3150",
        border="#3c4466",
        text_primary="#e7ebff",
        text_secondary="#aab3d9",
        accent="#7f8cff",
        accent_hover="#97a2ff",
        success="#45cf9e",
        warning="#ffd166",
        error="#ff6b6b",
    ),
    "RetroLight": ThemeTokens(
        name="RetroLight",
        bg="#ececec",
        surface="#ffffff",
        surface_alt="#f4f4f4",
        border="#c8c8c8",
        text_primary="#202020",
        text_secondary="#5f5f5f",
        accent="#2f80ed",
        accent_hover="#4d94ef",
        success="#1f9d55",
        warning="#b98a00",
        error="#d64545",
    ),
}


def build_stylesheet(tokens: ThemeTokens) -> str:
    """根据主题 token 生成全局样式。"""
    resources_dir = Path(__file__).resolve().parents[1] / "resources"
    up_arrow = (resources_dir / "spin_up.svg").as_posix()
    down_arrow = (resources_dir / "spin_down.svg").as_posix()
    return f"""
QMainWindow, QWidget {{
    background-color: {tokens.bg};
    color: {tokens.text_primary};
    font-size: 13px;
}}
QLabel {{
    background-color: transparent;
}}
QMenuBar, QMenu, QStatusBar, QToolBar {{
    background-color: {tokens.surface};
    color: {tokens.text_primary};
}}
QMenuBar::item:selected, QMenu::item:selected {{
    background-color: {tokens.surface_alt};
}}
QGroupBox {{
    background-color: {tokens.surface};
    border: 1px solid {tokens.border};
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {tokens.text_secondary};
}}
QLabel#subtle {{
    color: {tokens.text_secondary};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget, QTableWidget {{
    background-color: {tokens.surface_alt};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border};
    border-radius: 4px;
    padding: 5px;
}}
QCheckBox {{
    background-color: transparent;
    border: none;
    spacing: 6px;
    padding: 0;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid #8f8f8f;
    border-radius: 3px;
    background-color: #1b1b1b;
}}
QCheckBox::indicator:hover {{
    border-color: {tokens.accent_hover};
}}
QCheckBox::indicator:checked {{
    background-color: {tokens.accent};
    border-color: {tokens.accent};
}}
QSpinBox, QDoubleSpinBox {{
    padding-right: 20px;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 18px;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{up_arrow}");
    width: 12px;
    height: 12px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{down_arrow}");
    width: 12px;
    height: 12px;
}}
QSlider {{
    background-color: transparent;
}}
QSlider::groove:horizontal {{
    height: 4px;
    border-radius: 2px;
    background-color: {tokens.border};
}}
QSlider::sub-page:horizontal {{
    background-color: {tokens.accent};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 12px;
    margin: -5px 0;
    border-radius: 6px;
    background: {tokens.accent_hover};
}}
QHeaderView::section {{
    background-color: {tokens.surface};
    color: {tokens.text_secondary};
    border: 1px solid {tokens.border};
    padding: 6px;
}}
QPushButton {{
    background-color: {tokens.surface_alt};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border};
    border-radius: 4px;
    padding: 6px 12px;
}}
QPushButton:hover {{
    background-color: {tokens.border};
}}
QPushButton#primaryBtn {{
    background-color: {tokens.accent};
    color: #1a1a1a;
    border-color: {tokens.accent};
    font-weight: 700;
}}
QPushButton#primaryBtn:hover {{
    background-color: {tokens.accent_hover};
}}
QPushButton#dangerBtn {{
    background-color: {tokens.error};
    border-color: {tokens.error};
    color: white;
}}
QProgressBar {{
    background-color: {tokens.surface_alt};
    border: 1px solid {tokens.border};
    border-radius: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {tokens.accent};
    border-radius: 3px;
}}
QSplitter::handle {{
    background-color: transparent;
}}
"""

