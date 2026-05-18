import re

from qfluentwidgets import FluentIcon

from src.tasks.BaseEfTask import BaseEfTask


class Test(BaseEfTask):
    _round_robin_index = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "换队伍识别测试"
        self.description = "识别左下角换队伍编号并轮流换队（01-05 循环）。"
        self.icon = FluentIcon.SEARCH

    def run(self):
        selected_team = str((Test._round_robin_index % 5) + 1)
        Test._round_robin_index = (Test._round_robin_index + 1) % 5

        expected_text = f"0{selected_team}"
        team_switch_box = self.box_of_screen(0.0, 968/1080, 650/1920, 1.0, name="team_switch_left_bottom")
        expected_pattern = re.compile(rf"\b{re.escape(expected_text)}\b")

        self.log_info(
            f"开始换队伍识别并点击: 选项={selected_team}, 目标文本={expected_text}",
            notify=True,
        )

        results = self.wait_ocr(
            match=expected_pattern,
            box=team_switch_box,
            time_out=3,
            raise_if_not_found=False,
        )
        if not results:
            self.log_info(f"未识别到换队伍文本: {expected_text}", notify=True)
            return

        self.click(results[0], move_back=True, after_sleep=1.5)
        self.log_info(f"已识别并点击换队伍文本: {expected_text}", notify=True)
