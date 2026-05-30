"""自定义图标模块"""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

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


# ===== 预定义图标 =====
BATTLE = load_svg_icon("battle")
