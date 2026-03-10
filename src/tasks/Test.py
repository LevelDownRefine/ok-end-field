from src.tasks.AutoCombatTask import AutoCombatTask
from src.tasks.daily.auto_battle import auto_battle
from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask
import re
import time
battle_end_list=[fL.battle_end,fL.battle_end_small,fL.battle_end_big]
class Test(AutoCombatTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "测试"
        self.description = "完整战斗测试"
        self.default_config.update({
            "技能释放": "123",
            "启动技能点数": 2,
            "后台结束战斗通知": True,
            "无数字操作间隔": 6
        })
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

    def run(self):
        self.ensure_main()
        self.press_key('f8',after_sleep=2)
        self.wait_click_ocr(match=re.compile("索引"), time_out=5, after_sleep=2,box=self.box.top, log=True)
        if results:=self.wait_ocr(match=re.compile("前往"), time_out=5, box=self.box.right, log=True):
            self.log_info(f"检测到前往按钮，OCR结果: {results}")
            self.click(results[1],after_sleep=2)
        self.wait_click_ocr(match=re.compile("进入"), time_out=5, after_sleep=2, box=self.box.bottom_right, log=True)
        self.wait_click_ocr(match=re.compile("进入"), time_out=5, after_sleep=2, box=self.box.bottom_right, log=True)
        start_time= time.time()
        while not self.wait_ocr(match=re.compile("撤离"), time_out=1, box=self.box.top_left, log=True):
            if time.time() - start_time > 30:
                self.log_info("等待超时，未检测到撤离")
                return
        while not self.wait_ocr(match=re.compile("触碰"), time_out=1,  box=self.box.bottom_right, log=True):
            self.move_keys('w',duration=0.25)
        self.press_key("f")
        start_time=None
        while True:
            # 未进入战斗时短暂等待，进入后由 auto_battle 执行完整战斗流程
            if start_time and time.time() - start_time > 20:
                break
            battle_done = auto_battle(self, config=self.config)
            if not battle_done:
                self.sleep(0.1)
            else:
                start_time=time.time()
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
        while self.align_ocr_or_find_target_to_center(fL.battle_end, ocr=False, use_yolo=True, box=search_box, only_x=True, threshold=0.5, tolerance=100):
            if self.wait_ocr(match=re.compile("领取"), time_out=1, box=self.box.bottom_right):
                self.sleep(0.5)
                self.press_key("f",down_time=0.2)
                break
            else:
                self.move_keys('w', duration=0.25)
