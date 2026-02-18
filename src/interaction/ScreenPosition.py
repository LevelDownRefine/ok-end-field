from enum import Enum


class ScreenPosition(str, Enum):
    top_left = "top_left"
    top_right = "top_right"
    bottom_left = "bottom_left"
    bottom_right = "bottom_right"
    # 其他可能的位置
    left = "left"
    right = "right"
    top = "top"
    bottom = "bottom"
