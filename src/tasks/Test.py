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
        self.group_name = "工具与调试"
        self.description = "测试按键功能"

        self.interval = 0.3  # 读取间隔（秒）

    def run(self):
        while True:
            level = self.read_level()
            time.sleep(self.interval)
    def read_level(self):
            start_x = 0.125
            end_x = 0.802
            level_all = 11
            result= self.wait_feature(feature=fL.level_tip, time_out=10, raise_if_not_found=False, box=self.box_of_screen(0.120, 0.724, 0.803, 0.750))
            if not result:
                self.log_error("未找到等级信息标志")
                return None
            leve_x = result.x
            one_level_width = (end_x - start_x) / level_all
            level = int((leve_x - self.screen_width * start_x) / (self.screen_width * one_level_width))
            self.log_info(f"当前等级: {level}")
            return level