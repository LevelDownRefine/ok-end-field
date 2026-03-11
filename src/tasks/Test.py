from src.data.world_map import stages_list, stages_cost, higher_order_feature_dict
from src.data.world_map_utils import get_stage_category
from src.tasks.AutoCombatLogic import AutoCombatLogic
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask
from src.tasks.battle_mixin import BattleMixin
import re
import time
battle_end_list=[fL.battle_end,fL.battle_end_small,fL.battle_end_big]
class Test(BattleMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "测试"
        self.description = "完整战斗测试"
        self.stages_list=stages_list
        self.default_config = {
            "体力本":"干员经验",
            "技能释放": "123",
            "启动技能点数": 2,
            "后台结束战斗通知": True,
            "无数字操作间隔": 6
        }
        self.config_type["体力本"] = {"type": "drop_down", "options": self.stages_list}
        self.max_half_time=3
        self.lv_regex = re.compile(r"(?i)lv|\d{2}")
        self.last_op_time = 0
        self.last_skill_time = 0
        self.exit_check_count = 0  # 退出验证计数器，需要連续捐捕 2 次
        self._last_exit_fail_skill_count = None
        self.last_no_number_action_time = 0

    def test_times_ocr(self):
        box1 = self.box_of_screen(1749 / 1920, 107 / 1080, 1789 / 1920, 134 / 1080)
        box2 = self.box_of_screen(
            (1749 + (1832 - 1750)) / 1920,
            107 / 1080,
            (1789 + (1832 - 1750)) / 1920,
            134 / 1080,
        )
        self.wait_click_ocr(
            match=re.compile(r"^\d+/5$"),
            after_sleep=2,
            time_out=2,
            box=box1,
            log=True,
        )
        self.wait_click_ocr(
            match=re.compile(r"^\d+/5$"),
            after_sleep=2,
            time_out=2,
            box=box2,
            log=True,
        )
    def test_room_ocr(self):
        self.wait_click_ocr(match=[re.compile(i) for i in ["会客", "培养", "制造"]], time_out=5, after_sleep=2,log=True)
    def detect_ticket_number(self):
        result=self.wait_ocr(match=re.compile(r'^\d{1,3}/\d{1,3}$'),box=self.box_of_screen(1400/1920,0,1,70/1080),log=True)
        if result:
            ticket=int(result[0].name.split("/")[0])
            self.log_info(f"ticket:{ticket}")
            return ticket
        else:
            return 200
    def battle(self):
        stage_name=self.config.get("体力本")
        category_name= get_stage_category(stage_name)
        self.ensure_main()
        self.press_key('f8', after_sleep=2)
        self.wait_click_ocr(match=re.compile("索引"), time_out=5, after_sleep=2, box=self.box.top, log=True)
        left_ticket=self.detect_ticket_number()
        self.to_stage(stage_name,category_name)
        if category_name !="能量淤积点":
            self.battle_space(left_ticket,category_name)
        else:
            self.log_info("尚未实现能量淤积点功能",notify=True)
    def battle_space(self,left_ticket,category_name):
        self.wait_click_ocr(match=re.compile("进入"), time_out=5, after_sleep=2, box=self.box.bottom_right, log=True)
        enter_bool = False
        while left_ticket > 0:
            if enter_bool:
                self.wait_click_ocr(match=re.compile("重新挑战"), box=self.box.bottom_left, log=True)
            else:
                self.wait_click_ocr(match=re.compile("进入"), time_out=5, after_sleep=2, box=self.box.bottom_right,
                                    log=True)
                enter_bool = True
            if not self.to_battle():
                return False
            if not self.to_end():
                return False
            left_ticket = self.get_claim(stages_cost[category_name], left_ticket)
        return True

    def to_stage(self, stage_name, category_name):
        """
        通用关卡进入方法：
        1. 点击左侧类别。
        2. 定位关卡位置。
        3. 点击对应按钮（“前往”或“查看”）。
        4. 自动支持普通关卡和高阶关卡（危境预演）。
        """
        # 点击左侧关卡类别
        self.wait_click_ocr(
            match=re.compile(category_name),
            box=self.box.left,
            log=True,
            after_sleep=2
        )

        # 默认按钮文本
        to_text = "前往"

        # 判断是否是高阶关卡
        is_higher_order = category_name == "危境预演" and stage_name in higher_order_feature_dict

        if is_higher_order:
            # 高阶关卡，使用 feature_dict 查找位置
            location = self.find_one(feature_name=higher_order_feature_dict[stage_name])
        else:
            # 普通关卡
            location = self.wait_ocr(match=re.compile(stage_name), box=self.box.left, log=True)
            if category_name != "能量淤积点":
                to_text = "查看"

        # 如果找到位置，则点击按钮
        if location:
            self.wait_click_ocr(
                match=re.compile(to_text),
                box=self.box_of_screen(location[0].x, location[0].y, self.width, self.height),
                after_sleep=2
            )
    def to_battle(self):
        end_time = time.time()
        while not self.wait_ocr(match=re.compile("撤离"), time_out=1, box=self.box.top_left, log=True):
            if time.time() - end_time > 30:
                self.log_info("等待超时，进入协议空间超时")
                return False
        while not self.wait_ocr(match=re.compile("触碰"), time_out=1, box=self.box.bottom_right, log=True):
            self.move_keys('w', duration=0.25)
        self.press_key("f")
        return self.auto_battle()
    def run(self):
        self.to_end()
    def to_end(self):
        search_box = self.box_of_screen((1920 - 1550) / 1920, 0, 1550 / 1920, (1080 - 150) / 1080)
        for _ in range(5):
            if self.yolo_detect(fL.battle_end, box=search_box):
                break
            self.click(key="middle", after_sleep=2)
            self.move_keys('a', duration=0.01)
            self.sleep(2)

        self.align_ocr_or_find_target_to_center(
            fL.battle_end,
            ocr=False,
            use_yolo=True,
            box=search_box,
            max_time=5,
            only_x=True,
            raise_if_fail=False,
            threshold=0.5,
        )
        start_time=time.time()
        while self.align_ocr_or_find_target_to_center(fL.battle_end, ocr=False, use_yolo=True, box=search_box, only_x=True, threshold=0.5, tolerance=100):
            if time.time()-start_time>60:
                return False
            if self.wait_ocr(match=re.compile("领取"), time_out=1, box=self.box.bottom_right):
                self.sleep(0.5)
                self.press_key("f",down_time=0.2)
                break
            else:
                self.move_keys('w', duration=0.25)
        return True

    def get_claim(self, ticket_number, sum_ticket_number):
        """
        执行一次领奖操作，并返回剩余票数。

        逻辑：
        1. 等待界面稳定，并找到“可领取”提示。
        2. 尝试点击“获得奖励”，如果失败则本轮减少消耗票数。
        3. 扣除本轮票数，判断剩余票数是否足够。
        4. 点击“领取”，记录领取状态。
        5. 根据剩余票数和 max_half_time 判断下一轮是否可继续。

        返回：
            int: 扣掉本轮消耗票数后的剩余票数，如果票不足则返回 0。
        """
        self.wait_ui_stable(refresh_interval=1)
        start_time = time.time()

        # 等待界面出现“可领取”
        while not self.wait_ocr(match=re.compile("可领取"), box=self.box.top, time_out=1):
            if time.time() - start_time > 60:
                return 0
            self.press_key("f", down_time=0.2)
            self.wait_ui_stable(refresh_interval=1)

        # 本轮默认消耗票数
        need_ticket_number = ticket_number

        # 尝试点击“获得奖励”，失败则本轮减少消耗票数
        if self.max_half_time > 0:
            if not self.wait_click_ocr(
                    match=re.compile("获得奖励"),
                    box=self.box_of_screen(530 / 1920, 330 / 1080, 1400 / 1920, 570 / 1080),
                    time_out=2,
                    log=True
            ):
                need_ticket_number = ticket_number - 40  # 减耗票逻辑
                self.max_half_time -= 1  # 减耗次数减少

        # 扣除本轮消耗票数
        sum_ticket_number -= need_ticket_number
        if sum_ticket_number < 0:
            return 0  # 票不足，不能继续

        # 点击“领取”，失败则返回0
        if not self.wait_click_ocr(match=re.compile("领取"), box=self.box.bottom_right, time_out=2, log=True):
            self.log_info("领取失败")
            return 0

        # 如果减耗次数用完，下一轮恢复全额消耗
        if self.max_half_time <= 0:
            need_ticket_number = ticket_number

        # 预测下一轮是否还能继续
        next_sum = sum_ticket_number - need_ticket_number
        # 返回本轮剩余票数，不返回next_sum，因为减耗只用于判断下一轮可否继续
        return sum_ticket_number

