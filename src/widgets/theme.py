"""
主题系统：Fusion 风格 + QPalette 驱动，仅保留最小 QSS 覆盖。

原则：所有标准控件（ComboBox、SpinBox、CheckBox、Slider、ScrollBar、
ProgressBar、TabWidget 等）全部由 Fusion + QPalette 渲染，
QSS 只用于 QPalette 无法实现的差异化样式。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeTokens:
    name: str
    bg: str
    surface: str
    surface_alt: str
    surface_elevated: str
    border: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_on_accent: str
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
        surface_elevated="#383838",
        border="#4a4a4a",
        text_primary="#f2f2f2",
        text_secondary="#b5b5b5",
        text_muted="#8b8b9b",
        text_on_accent="#1a1a1a",
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
        surface_elevated="#323966",
        border="#3c4466",
        text_primary="#e7ebff",
        text_secondary="#aab3d9",
        text_muted="#7a83aa",
        text_on_accent="#0d0f1a",
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
        surface_elevated="#fafafa",
        border="#c8c8c8",
        text_primary="#202020",
        text_secondary="#5f5f5f",
        text_muted="#8a8a8a",
        text_on_accent="#ffffff",
        accent="#2f80ed",
        accent_hover="#4d94ef",
        success="#1f9d55",
        warning="#b98a00",
        error="#d64545",
    ),
}


def build_palette_from_tokens(tokens: ThemeTokens):
    """根据 ThemeTokens 构建 QPalette，Fusion 风格的全部颜色由此驱动。"""
    from PyQt5.QtGui import QPalette, QColor
    from PyQt5.QtCore import Qt

    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(tokens.bg))
    palette.setColor(QPalette.WindowText, QColor(tokens.text_primary))
    palette.setColor(QPalette.Base, QColor(tokens.surface_alt))
    palette.setColor(QPalette.AlternateBase, QColor(tokens.surface))
    palette.setColor(QPalette.ToolTipBase, QColor(tokens.surface_elevated))
    palette.setColor(QPalette.ToolTipText, QColor(tokens.text_primary))
    palette.setColor(QPalette.Text, QColor(tokens.text_primary))
    palette.setColor(QPalette.Button, QColor(tokens.surface_alt))
    palette.setColor(QPalette.ButtonText, QColor(tokens.text_primary))
    palette.setColor(QPalette.BrightText, QColor(tokens.error))
    palette.setColor(QPalette.Highlight, QColor(tokens.accent))
    palette.setColor(QPalette.HighlightedText, QColor(tokens.text_on_accent))
    palette.setColor(QPalette.Link, QColor(tokens.accent))
    palette.setColor(QPalette.Mid, QColor(tokens.border))
    palette.setColor(QPalette.Dark, QColor(tokens.border))
    palette.setColor(QPalette.Shadow, QColor(tokens.bg))
    palette.setColor(QPalette.Light, QColor(tokens.surface_elevated))
    palette.setColor(QPalette.Midlight, QColor(tokens.surface))

    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(tokens.text_muted))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(tokens.text_muted))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(tokens.text_muted))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(tokens.border))

    return palette


def build_stylesheet(tokens: ThemeTokens) -> str:
    """最小 QSS：只包含 QPalette 无法实现的差异化样式。"""
    return f"""
/* ── QLabel 按 objectName 区分颜色（QPalette 不支持） ── */
QLabel#subtle {{
    color: {tokens.text_secondary};
}}
QLabel#muted {{
    color: {tokens.text_muted};
}}
QLabel#badge {{
    color: {tokens.text_secondary};
    background-color: {tokens.surface};
    border: 1px solid {tokens.border};
    border-radius: 3px;
    padding: 2px 8px;
    font-size: 12px;
}}
QLabel#signatureLabel {{
    color: {tokens.text_muted};
    padding-right: 8px;
}}

/* ── QPushButton 按 objectName 区分主/危险按钮（QPalette 不支持） ── */
QPushButton#primaryBtn {{
    background-color: {tokens.accent};
    color: {tokens.text_on_accent};
    border: 1px solid {tokens.accent};
    font-weight: 700;
}}
QPushButton#primaryBtn:hover {{
    background-color: {tokens.accent_hover};
    border-color: {tokens.accent_hover};
}}
QPushButton#primaryBtn:pressed {{
    background-color: {tokens.accent};
    border-color: {tokens.accent};
}}
QPushButton#dangerBtn {{
    background-color: {tokens.error};
    color: {tokens.text_on_accent};
    border: 1px solid {tokens.error};
}}
QPushButton#dangerBtn:hover {{
    background-color: {tokens.error};
    border-color: {tokens.error};
}}
"""


def build_dialog_stylesheet(tokens: ThemeTokens) -> str:
    """对话框最小 QSS：只包含 QPalette 无法实现的 QLabel / QFrame 差异化样式。"""
    return f"""
/* ── QLabel 差异化 ── */
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    color: {tokens.accent};
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {tokens.text_secondary};
}}
QLabel#key {{
    color: {tokens.text_secondary};
    font-weight: 600;
}}
QLabel#valueAccent {{
    color: {tokens.accent};
    font-weight: 500;
}}
QLabel#muted {{
    color: {tokens.text_muted};
}}
QLabel#titleLabel {{
    font-size: 16px;
    font-weight: 700;
}}
QLabel#valueLabel {{
    color: {tokens.accent};
    font-weight: 500;
}}

/* ── QFrame 卡片（QPalette 无法按 objectName 区分） ── */
QFrame#card {{
    background-color: {tokens.surface};
    border: 1px solid {tokens.border};
    border-radius: 6px;
}}

/* ── QPushButton 差异化 ── */
QPushButton#primary {{
    background-color: {tokens.accent};
    color: {tokens.text_on_accent};
    border: 1px solid {tokens.accent};
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background-color: {tokens.accent_hover};
    border-color: {tokens.accent_hover};
}}
QPushButton#secondaryBtn:hover {{
    background-color: {tokens.border};
}}
"""
