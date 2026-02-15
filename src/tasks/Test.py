import time
from src.interaction.ScreenPosition import ScreenPosition as sP
from src.tasks.BaseEfTask import BaseEfTask
from src.interaction.Mouse import active_and_send_mouse_delta,run_at_window_pos
import pyautogui
import re
class Test(BaseEfTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "测试"

    def in_friend_boat(self):
        return self.wait_ocr(match=re.compile("离开"), box=sP.TOP_LEFT.value)
    def ensure_in_friend_boat(self):
        start_time = time.time()
        while True:
            if time.time() - start_time > 30:
                self.log_info("进入好友帝江号超时" )
                return False
            if self.in_friend_boat():
                return True
    def run(self):
        self.ensure_in_friend_boat()
        self.active_and_send_mouse_delta(self.hwnd.hwnd, dx=self.width//-2, dy=0, activate=True, only_activate=False, delay=0.2, steps=3)
        self.log_info("开始前往干员联络站")
        self.send_key("m", after_sleep=2)
        self.log_info("打开地图界面 (按下 M)")

        # 查找联络站特征
        result = self.find_one(
            feature_name="market_dispatch_terminal",
            box=self.box_of_screen(0, 0, 1, 1),
            threshold=0.7,
        )
        if not result:
            self.log_info("未找到干员联络站图标")
            return
        self.log_info("找到干员联络站图标，点击进入")
        self.click(result, after_sleep=2)

        # 查找追踪按钮
        if result := self.wait_ocr(
            match=re.compile("追踪"), box=sP.BOTTOM_RIGHT.value, time_out=5
        ):
            if (
                "追踪" in result[0].name
                and "取" not in result[0].name
                and "消" not in result[0].name
            ):
                self.log_info("点击追踪按钮")
                self.click(result, after_sleep=2)

        self.send_key("m", after_sleep=2)
        self.log_info("关闭地图界面 (按下 M)")
        self.align_ocr_or_find_target_to_center(
            ocr_match_or_feature_name_list="market_dispatch_terminal_out",
            only_x=True,
            threshold=0.7,
            ocr=False,
        )
        self.log_info("已对齐地图目标")

        # 开始移动到联络台
        start_time = time.time()
        short_distance_flag = False
        fail_count = 0

        while not self.wait_ocr(
            match=re.compile("物资调度终端"), box=sP.BOTTOM_RIGHT.value, time_out=1
        ):
            if time.time() - start_time > 200:
                self.log_info("前往干员联络站超时")
                return
            if not short_distance_flag:
                nav = self.find_feature(
                    "market_dispatch_terminal_out",
                    box=self.box_of_screen(
                        (1920 - 1550) / 1920,
                        150 / 1080,
                        1550 / 1920,
                        (1080 - 150) / 1080,
                    ),
                    threshold=0.7,
                )
                if nav:
                    fail_count = 0
                    self.log_info("找到导航路径，继续对齐并前进")
                    self.align_ocr_or_find_target_to_center(
                        ocr_match_or_feature_name_list="market_dispatch_terminal_out",
                        only_x=True,
                        threshold=0.7,
                        ocr=False,
                    )
                    self.move_keys("w", duration=1)
                else:
                    fail_count += 1
                    self.log_info(f"未找到导航路径，连续失败次数: {fail_count}")
                    if fail_count >= 3:
                        self.log_info("长时间未找到导航，切换短距离移动")
                        short_distance_flag = True
                    self.move_keys("w", duration=0.5)
            else:
                self.move_keys("w", duration=0.5)
        self.send_key("f", after_sleep=2)
        # self.wait_click_ocr(match=re.compile('输入名称'), settle_time=0.5)
        # self.input_text('test')
        # active_and_send_mouse_delta(self.hwnd.hwnd, dx=100, dy=100, activate=True, only_activate=True, delay=0.02, steps=3)
        # self.sleep(5)
        # for _ in range(12):
        #     pyautogui.scroll(500)  # 向上滚
        # count = 0
        # while True:
        #     if count >=30:
        #         break
        #     self.find_feature(
        #         feature_name="chat_icon",
        #         box=self.box_of_screen(
        #             1260 / 1920, 699 / 1080, (1260 + 41) / 1920, 699 + 273 / 1080
        #         ),
        #     )
        #     self.sleep(1)
        #     count += 1
