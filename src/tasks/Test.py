import time
import re
from src.data.FeatureList import FeatureList as fL
from src.image.hsv_config import HSVRange as hR
from src.tasks.BaseEfTask import BaseEfTask
from src.tasks.mixin.navigation_mixin import NavigationMixin

class Test(NavigationMixin):
    """
    简单箭头角度读取测试
    直接调用 get_arrow_angle() 并持续输出当前角度
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "按键测试"
        self.description = "测试按键功能"

        self.interval = 0.3  # 读取间隔（秒）

    def run(self):
        self.wait_click_feature(
                feature=fL.battle_cost_x1,
                time_out=2,
                after_sleep=1,
                horizontal_variance=0.15,
                raise_if_not_found=False,
        )
