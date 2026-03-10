import re
import time
import cv2
import numpy as np
from qfluentwidgets import FluentIcon
from ok import TriggerTask, Logger
from src.tasks.BaseEfTask import BaseEfTask
from src.tasks.battle_mixin import BattleMixin
from src.data.FeatureList import FeatureList as fL
logger = Logger.get_logger(__name__)



# 自动战斗主逻辑独立类
class AutoCombatLogic:
    def __init__(self, task: BaseEfTask):
        self.task = task

    def run(self):
        task = self.task
        in_combat_check = task.in_combat(required_yellow=1)
        task.log_info(f"进入战斗检查: in_combat={in_combat_check}")

        if not in_combat_check:
            task.log_info("未检测到战斗状态,退出自动战斗")
            return  False

        task.log_info("检测到进入战斗,开始自动战斗流程")
        raw_skill_config = task.config.get("技能释放", "123")
        start_trigger_count = task.config.get("启动技能点数", 2)
        skill_sequence = task._parse_skill_sequence(raw_skill_config)
        task.log_info(f"战斗配置: 技能序列={skill_sequence}, 启动点数={start_trigger_count}")

        if task.debug:
            task.screenshot('enter_combat')

        task.click(key='middle')

        while True:
            skill_count = task.get_skill_bar_count()
            if task.is_combat_ended():
                if task.debug:
                    task.screenshot('out_of_combat')
                task.log_info("自动战斗结束!", notify=task.config.get("后台结束战斗通知") and task.in_bg())
                task.log_info("退出战斗主循环")
                break

            task.handle_no_damage_number_actions()

            if task.use_link_skill() or task.use_ult():
                continue

            if skill_count >= start_trigger_count:
                task.log_info(f"Triggering sequence at {skill_count} points")
                for skill_key in skill_sequence:
                    if not task.in_combat():
                        break
                    while True:
                        current_points = task.get_skill_bar_count()
                        time_since_last_skill = time.time() - task.last_skill_time
                        if current_points >= 1 and time_since_last_skill >= 1.0:
                            break
                        if task.use_link_skill() or task.use_ult():
                            continue
                        if current_points < 0 and (task.ocr_lv() or not task.in_team()):
                            break
                        task.handle_no_damage_number_actions()
                        task.perform_attack_weave()
                        task.sleep(0.02)
                    if not task.in_combat():
                        break
                    task.send_key(skill_key)
                    task.last_skill_time = time.time()
                    task.last_op_time = time.time()
                    task.log_info(f"Used skill {skill_key}")
                task.log_info("Sequence finished, returning to charge mode")
            else:
                task.perform_attack_weave()
            task.sleep(0.02)
        return True

# 原有任务类调用独立逻辑
class AutoCombatTask(BaseEfTask, BattleMixin, TriggerTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_config = {'_enabled': False}
        self.name = "自动战斗"
        self.description = "自动战斗(进入战斗后自动战斗直到结束)"
        self.icon = FluentIcon.ACCEPT
        self.default_config.update({
            "技能释放": "123",
            "启动技能点数": 2,
            "后台结束战斗通知": True,
            "平A间隔": 0.12,
            "无数字操作间隔": 6
        })
        self.config_description.update({
            "技能释放": "满技能时, 开始释放技能, 如123, 建议只放3个技能",
            "启动技能点数": "当技能点达到该数值时，开始执行技能序列, 1-3",
            "平A间隔": "平A点击间隔(秒), 越小越快, 建议 0.08~0.15",
            "无数字操作间隔": "战斗中周期触发锁敌+向前闪避的最小间隔(秒，最少6秒)",
        })
        self.lv_regex = re.compile(r"(?i)lv|\d{2}")
        self.last_op_time = 0
        self.last_skill_time = 0
        self.exit_check_count = 0
        self._last_exit_fail_skill_count = None
        self.last_no_number_action_time = 0
        self._combat_logic = AutoCombatLogic(self)

    def run(self):
        self._combat_logic.run()

