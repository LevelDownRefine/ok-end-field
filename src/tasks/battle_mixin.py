import time
import re
import cv2
import numpy as np

class BattleMixin:
    def _parse_skill_sequence(self, raw_config: str) -> list[str]:
        if not raw_config:
            return []
        trimmed_config = raw_config.strip()
        sequence = []
        valid_skills = {'1', '2', '3', '4'}
        for char in trimmed_config:
            if char in valid_skills:
                sequence.append(char)
        return sequence if sequence else ['1', '2', '3']

    def use_ult(self):
        ults = ['1', '2', '3', '4']
        for ult in ults:
            if self.find_one("ult_" + ult):
                self.send_key_down(ult)
                self.wait_until(lambda: not self.in_combat())
                self.send_key_up(ult)
                self.wait_in_combat(time_out=8)
                self.last_op_time = time.time()
                return True
        return False

    def use_link_skill(self):
        if self.find_one("default_link_skill", threshold=0.7):
            self.send_key("e")
            self.last_op_time = time.time()
            return True
        return False

    def in_combat(self, required_yellow=0):
        return self.get_skill_bar_count() >= required_yellow and self.in_team() and not self.ocr_lv()

    def in_team(self):
        return all([
            self.find_one('skill_1') is not None,
            self.find_one('skill_2') is not None,
            self.find_one('skill_3') is not None,
            self.find_one('skill_4') is not None,
        ])

    def is_combat_ended(self):
        if self._check_single_exit_condition():
            self.exit_check_count += 1
            if self.exit_check_count >= 2:
                self.exit_check_count = 0
                return True
        else:
            self.exit_check_count = 0
        return False

    def _check_single_exit_condition(self):
        skill_count = self.get_skill_bar_count()
        if skill_count >= 0:
            if getattr(self, '_last_exit_fail_skill_count', None) != skill_count:
                self.log_info(f"退出检查失败: 技能条仍有效 (count={skill_count})")
                self._last_exit_fail_skill_count = skill_count
            return False
        self._last_exit_fail_skill_count = None
        has_lv = self.ocr_lv()
        in_team = self.in_team()
        if not (has_lv or not in_team):
            self.log_info(f"退出检查失败: UI状态不符 (has_lv={has_lv}, in_team={in_team})")
            return False
        has_center_number = self._check_center_area_has_number()
        if has_center_number:
            self.log_info("退出检查失败: 中间区域仍有伤害数字")
            return False
        self.log_info(f"退出检查通过: skill_count={skill_count}, has_lv={has_lv}, in_team={in_team}, center_number={has_center_number}")
        return True

    def _check_center_area_has_number(self):
        try:
            box = self.box_of_screen(0.20, 0.00, 0.80, 0.65)
            self.next_frame()
            center_area = self.ocr(
                match=r"^\d+$",
                box=box,
                name="center_number"
            )
            if len(center_area) > 0:
                self.log_info(f"中间区域识别到数字: {[r.name for r in center_area]}")
            return len(center_area) > 0
        except Exception:
            return False

    def handle_no_damage_number_actions(self):
        interval = self.config.get("无数字操作间隔", 6)
        interval = max(6.0, min(float(interval), 30.0))
        if time.time() - getattr(self, 'last_no_number_action_time', 0) < interval:
            return
        self.log_info("战斗中周期触发：执行索敌+向前闪避（贴近敌人）")
        self.click(key='middle', down_time=0.002)
        self.dodge_forward(pre_hold=0.05, dodge_down_time=0.03, after_sleep=0.02)
        self.last_no_number_action_time = time.time()
        self.last_op_time = time.time()

    def perform_attack_weave(self):
        attack_interval = self.config.get("平A间隔", 0.12)
        attack_interval = max(0.03, min(float(attack_interval), 0.5))
        if time.time() - getattr(self, 'last_op_time', 0) > attack_interval:
            self.click(move=False, key='left', down_time=0.005)
            self.last_op_time = time.time()
    def perform_attack_weave(self):
        """Performs a normal attack if the 0.3s operation interval permits."""
        attack_interval = self.config.get("平A间隔", 0.12)
        attack_interval = max(0.03, min(float(attack_interval), 0.5))
        if time.time() - self.last_op_time > attack_interval:
            # 明确指定左键，缩短按下时间，减少漏点概率
            self.click(move=False, key='left', down_time=0.005)
            self.last_op_time = time.time()

    def handle_no_damage_number_actions(self):
        interval = self.config.get("无数字操作间隔", 6)
        interval = max(6.0, min(float(interval), 30.0))
        if time.time() - self.last_no_number_action_time < interval:
            return
        self.log_info("战斗中周期触发：执行索敌+向前闪避（贴近敌人）")
        self.click(key='middle', down_time=0.002)
        self.dodge_forward(pre_hold=0.05, dodge_down_time=0.03, after_sleep=0.02)
        self.last_no_number_action_time = time.time()
        self.last_op_time = time.time()

    def _parse_skill_sequence(self, raw_config: str) -> list[str]:
        if not raw_config:
            return []
        trimmed_config = raw_config.strip()
        sequence = []
        valid_skills = {'1', '2', '3', '4'}
        for char in trimmed_config:
            if char in valid_skills:
                sequence.append(char)
        return sequence if sequence else ['1', '2', '3']

    def use_ult(self):
        ults = ['1', '2', '3', '4']
        for ult in ults:
            if self.find_one("ult_" + ult):
                self.send_key_down(ult)
                self.wait_until(lambda: not self.in_combat())
                self.send_key_up(ult)
                self.wait_in_combat(time_out=8)
                self.last_op_time = time.time()
                return True
        return False

    def wait_in_combat(self, time_out=3, click=False):
        start = time.time()
        while time.time() - start < time_out:
            if self.in_combat():
                return True
            elif click:
                self.perform_attack_weave()
            else:
                self.sleep(0.003)

    def is_combat_ended(self):
        """
        检查战斗是否已结束。
        返回 True 表示战斗结束，False 表示战斗继续。
        
        退出条件（需要連续验证 2 次）：
        1. 技能条判定为 -1（无有效技能条）
        2. 且满足以下任一条件：
           - OCR 识别到 LV（战斗外 UI）
           - 队伍图标不完整（in_team 返回 False）
        3. 中间区域没有数字（不是伤害数字浮动）
        """
        # 检查是否满足退出条件
        if self._check_single_exit_condition():
            self.exit_check_count += 1
            # 需要連续捐捕 2 次
            if self.exit_check_count >= 2:
                self.exit_check_count = 0  # 重置计数器
                return True
        else:
            # 敢不满足条件时，重置计数器
            self.exit_check_count = 0

        return False

    def _check_single_exit_condition(self):
        """
        检查单次退出条件，返回 True 为满足条件。
        """
        skill_count = self.get_skill_bar_count()

        # 第一步：技能条判定
        if skill_count >= 0:
            # 避免高频重复刷屏，仅在 count 变化时打印
            if self._last_exit_fail_skill_count != skill_count:
                self.log_info(f"退出检查失败: 技能条仍有效 (count={skill_count})")
                self._last_exit_fail_skill_count = skill_count
            return False
        self._last_exit_fail_skill_count = None

        # 第二步：UI 状态判定
        has_lv = self.ocr_lv()
        in_team = self.in_team()

        if not (has_lv or not in_team):
            self.log_info(f"退出检查失败: UI状态不符 (has_lv={has_lv}, in_team={in_team})")
            return False

        # 第三步：检查中间区域是否有数字（伤害数字）
        # 如果中间有数字，表示战斗仍在进行（伤害数字浮动）
        has_center_number = self._check_center_area_has_number()
        if has_center_number:
            self.log_info("退出检查失败: 中间区域仍有伤害数字")
            return False

        self.log_info(f"退出检查通过: skill_count={skill_count}, has_lv={has_lv}, in_team={in_team}, center_number={has_center_number}")
        return True

    def _check_center_area_has_number(self):
        """检查屏幕中间区域是否有数字（伤害数字）"""
        try:
            # 检测区域：横向加宽，纵向从顶部到中部（向上扩展）
            box = self.box_of_screen(0.20, 0.00, 0.80, 0.65)
            self.next_frame()
            center_area = self.ocr(
                match=r"^\d+$",
                box=box,
                name="center_number"
            )
            if len(center_area) > 0:
                self.log_info(f"中间区域识别到数字: {[r.name for r in center_area]}")
            return len(center_area) > 0
        except Exception:
            return False

    def ocr_lv(self):
        lv = self.ocr(0.02, 0.89, 0.23, 0.93, match=self.lv_regex, name='lv_text')
        if len(lv) > 0:
            return True
        lv = self.ocr(0.02, 0.89, 0.23, 0.93, frame_processor=isolate_white_text_to_black, match=self.lv_regex,
                      name='lv_text')
        return len(lv) > 0

    def use_link_skill(self):
        """释放连携技（从配置中读取实际键位）"""
        if self.find_one("default_link_skill", threshold=0.7):
            self.send_key("e")
            self.last_op_time = time.time()
            return True
        return False

    def in_combat(self, required_yellow=0):
        return self.get_skill_bar_count() >= required_yellow and self.in_team() and not self.ocr_lv()

    def in_team(self):
        return all([
            self.find_one('skill_1') is not None,
            self.find_one('skill_2') is not None,
            self.find_one('skill_3') is not None,
            self.find_one('skill_4') is not None,
        ])

    def get_skill_bar_count(self):
        skill_area_box = self.box_of_screen_scaled(3840, 2160, 1586, 1940, 2266, 1983)
        # self.draw_boxes('skill_area', skill_area_box, color='yellow', debug=True)
        # self.log_debug(f'skill_area_box {skill_area_box}')
        skill_area = skill_area_box.crop_frame(self.frame)
        # self.screenshot('skill_area', frame=skill_area)
        if not has_rectangles(skill_area):
            return -1

        count = 0
        y_start, y_end = 1958, 1970

        bars = [
            (1604, 1796),
            (1824, 2013),
            (2043, 2231)
        ]

        for x1, x2 in bars:
            if self.check_is_pure_color_in_4k(x1, y_start, x2, y_end, yellow_skill_color):
                count += 1
            else:
                break

        if count == 0:
            has_white_left = self.check_is_pure_color_in_4k(1604, y_start, 1614, y_end, white_skill_color,
                                                            threshold=0.1)
            if not has_white_left:
                count = -1
        return count

    def check_is_pure_color_in_4k(self, x1, y1, x2, y2, color_range=None, threshold=0.9):
        skill_area_box = self.box_of_screen_scaled(3840, 2160, x1, y1, x2, y2)
        bar = skill_area_box.crop_frame(self.frame)

        if bar.size == 0:
            return False

        height, width, _ = bar.shape
        consecutive_matches = 0

        for i in range(height):
            row_pixels = bar[i]
            unique_colors, counts = np.unique(row_pixels, axis=0, return_counts=True)
            most_frequent_index = np.argmax(counts)
            dominant_count = counts[most_frequent_index]
            dominant_color = unique_colors[most_frequent_index]

            is_valid_row = (dominant_count / width) >= threshold

            if is_valid_row and color_range:
                b, g, r = dominant_color
                if not (color_range['r'][0] <= r <= color_range['r'][1] and
                        color_range['g'][0] <= g <= color_range['g'][1] and
                        color_range['b'][0] <= b <= color_range['b'][1]):
                    is_valid_row = False

            if is_valid_row:
                consecutive_matches += 1
                if consecutive_matches >= 2:
                    return True
            else:
                consecutive_matches = 0

        return False


def has_rectangles(frame):
    if frame is None:
        return False

    original_h, original_w = frame.shape[:2]
    scale_factor = 4
    resized = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_width = (original_w * scale_factor) * 0.25

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > min_width and w > h and h > 10:
            return True

    return False


lower_white_none_inclusive = np.array([222, 222, 222], dtype=np.uint8)
black = np.array([0, 0, 0], dtype=np.uint8)


def isolate_white_text_to_black(cv_image):
    match_mask = cv2.inRange(cv_image, black, lower_white_none_inclusive)
    output_image = cv2.cvtColor(match_mask, cv2.COLOR_GRAY2BGR)
    return output_image


yellow_skill_color = {
    'r': (230, 255),
    'g': (180, 255),
    'b': (0, 85)
}

white_skill_color = {
    'r': (190, 255),
    'g': (190, 255),
    'b': (190, 255)
}
