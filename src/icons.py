"""自定义图标模块"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from qfluentwidgets import FluentIconBase, Theme, isDarkTheme

_ICONS_DIR = Path("assets") / "icons"


def _get_icon_path(name: str) -> str:
    """获取图标文件路径"""
    return str(_ICONS_DIR / f"{name}.svg")


def load_svg_icon(name: str, color: str = None) -> QIcon:
    """
    加载 SVG 图标，可选自定义颜色

    Args:
        name: 图标名称 (不含 .svg 后缀)
        color: 可选颜色，如 '#FF5722' 或 'red'

    Returns:
        QIcon 对象
    """
    path = _get_icon_path(name)
    if not Path(path).exists():
        return QIcon()

    if color is None:
        return QIcon(path)

    renderer = QSvgRenderer(path)
    pixmap = QPixmap(renderer.defaultSize())
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    return QIcon(pixmap)


def load_png_icon(name: str) -> QIcon:
    """
    加载 PNG 图标

    Args:
        name: 图标名称 (不含 .png 后缀)

    Returns:
        QIcon 对象
    """
    path = str(_ICONS_DIR / f"{name}.png")
    if not Path(path).exists():
        return QIcon()
    return QIcon(path)


def load_theme_png_icon(light_name: str, dark_name: str) -> QIcon:
    """
    根据当前主题加载对应的 PNG 图标

    Args:
        light_name: 浅色主题图标名称 (不含 .png 后缀)
        dark_name: 深色主题图标名称 (不含 .png 后缀)

    Returns:
        QIcon 对象
    """
    if isDarkTheme():
        name = dark_name
    else:
        name = light_name
    path = str(_ICONS_DIR / f"{name}.png")
    if not Path(path).exists():
        return QIcon()
    return QIcon(path)


class ThemePngIcon(FluentIconBase):
    """根据主题自动切换的 PNG 图标，dark/light 指图标文件本身的主题色"""

    def __init__(self, light_icon: str, dark_icon: str):
        """
        Args:
            light_icon: 浅色图标文件名 (不含 .png 后缀)
            dark_icon: 深色图标文件名 (不含 .png 后缀)
        """
        self._light_path = str(_ICONS_DIR / f"{light_icon}.png")
        self._dark_path = str(_ICONS_DIR / f"{dark_icon}.png")

    def path(self, theme=Theme.AUTO):
        if theme == Theme.AUTO:
            is_dark = isDarkTheme()
        else:
            is_dark = theme == Theme.DARK
        return self._dark_path if is_dark else self._light_path


# ===== 预定义图标 =====
BATTLE = load_svg_icon("battle")
DELIVERY = ThemePngIcon("delivery_dark", "delivery_light")
