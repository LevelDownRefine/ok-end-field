from src.data.world_map import stages_list, stages_cost, higher_order_feature_dict
from src.data.world_map_utils import get_stage_category
from src.tasks.AutoCombatLogic import AutoCombatLogic
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask
from src.tasks.battle_mixin import BattleMixin
from qfluentwidgets import FluentIcon
from src.tasks.daily.liaison_mixin import DailyLiaisonMixin
import re
import time



class BattleTask(DailyLiaisonMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "刷体力"
        self.description = "刷体力任务"
        self.stages_list = stages_list
        self.icon = FluentIcon.BRIGHTNESS
        self.default_config = {
            "体力本": "干员经验",
            "技能释放": "123",
            "启动技能点数": 2,
            "后台结束战斗通知": True,
            "无数字操作间隔": 6,
            "进入战斗后的初始等待时间": 3
        }
        self.config_type["体力本"] = {"type": "drop_down", "options": self.stages_list}
        self.max_half_time = 3
        self.lv_regex = re.compile(r"(?i)lv|\d{2}")
        self.last_op_time = 0
        self.last_skill_time = 0
        self.exit_check_count = 0  # 退出验证计数器，需要連续捐捕 2 次
        self._last_exit_fail_skill_count = None
        self.last_no_number_action_time = 0

    def run(self):
        if self.battle():
            self.log_info("刷体力结束!", notify=self.config.get("后台结束战斗通知") and self.in_bg())
        else:
            self.log_info("未检测到刷体力正常结束,可能未进入战斗或战斗异常,请检查")
