import random
import re
import time
import threading
import cv2
import imagehash
import numpy as np
import pyautogui

from functools import partial
from typing import List
from enum import Enum
from PIL import Image
from ok import BaseTask, Box
from skimage.metrics import structural_similarity as ssim

from src.data.FeatureList import FeatureList
from src.image.frame_processs import isolate_by_hsv_ranges
from src.image.yolo_detector import YoloDetector
from src.essence.essence_recognizer import EssenceInfo, read_essence_info
from src.interaction.Key import move_keys
from src.interaction.Mouse import active_and_send_mouse_delta, move_to_target_once, run_at_window_pos
from src.interaction.ScreenPosition import ScreenPosition
from src.interaction.KeyConfig import KeyConfigManager

TOLERANCE = 50


class BaseEfTask(BaseTask):
    """游戏自动化任务基类，提供通用的交互和识别功能"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logged_in = False  # 记录是否已登录游戏
        self.box = ScreenPosition(self)  # 屏幕位置辅助对象，提供top/bottom/left/right等边界
        self.key_config = self.get_global_config('Game Hotkey Config')  # 获取全局热键配置
        self.key_manager = KeyConfigManager(self.key_config)  # 初始化热键管理器
        # 初始化 YOLO 检测器

        self._yolo_detector = None  # YOLO 检测器实例
        self._yolo_model_path = None
        self._yolo_loading = False
        self._yolo_loaded_event = threading.Event()
        self._start_yolo_loading_thread()

    def _start_yolo_loading_thread(self):
        def load_yolo():
            self._yolo_loading = True
            try:
                from src.config import config as app_config
                yolo_config = app_config.get("yolo", {})
                model_path = yolo_config.get("model_path", "models/yolo/best.pt")
                from src.image.yolo_detector import YoloDetector
                self._yolo_detector = YoloDetector(model_path=model_path)
                self._yolo_model_path = model_path
            finally:
                self._yolo_loading = False
                self._yolo_loaded_event.set()
        threading.Thread(target=load_yolo, daemon=True).start()

    @property
    def yolo_detector(self):
        if self._yolo_detector is not None:
            return self._yolo_detector
        # 如果还在加载，等待加载完成
        if self._yolo_loading:
            self._yolo_loaded_event.wait()
            return self._yolo_detector
        # 如果未启动加载（极端情况），直接加载
        from src.config import config as app_config
        yolo_config = app_config.get("yolo", {})
        model_path = yolo_config.get("model_path", "models/yolo/best.pt")
        from src.image.yolo_detector import YoloDetector
        self._yolo_detector = YoloDetector(model_path=model_path)
        self._yolo_model_path = model_path
        return self._yolo_detector

    def press_key(self, key: str, down_time: float = 0.02, after_sleep: float = 0, interval: int = -1):
        """发送通用部分的游戏热键。
        
        先从配置中查询是否有该键的自定义映射，如果没有则直接使用传入的键值。
        
        Args:
            key: 按键值（如 'q', 'e', 'f1' 等），系统会先检查配置中是否有映射
            down_time: 按键按下持续时间（秒）
            after_sleep: 发送后额外等待时间（秒）
            interval: 按键间隔
            
        Returns:
            send_key 的返回值
            
        Example:
            self.press_key('m', after_sleep=0.5)           # 地图键
            self.press_key('b')                            # 背包键
            self.press_key('f8', after_sleep=1)            # 行动手册键
        """
        actual_key = self.key_manager.resolve_common_key(key)
        return self.send_key(actual_key, interval=interval, down_time=down_time, after_sleep=after_sleep)

    def press_industry_key(self, key: str, down_time: float = 0.02, after_sleep: float = 0, interval: int = -1):
        """发送集成工业部分的游戏热键。
        
        先从配置中查询是否有该键的自定义映射，如果没有则直接使用传入的键值。
        
        Args:
            key: 按键值（如 'q', 'e', 'capslock' 等），系统会先检查配置中是否有映射
            down_time: 按键按下持续时间（秒）
            after_sleep: 发送后额外等待时间（秒）
            interval: 按键间隔
            
        Returns:
            send_key 的返回值
            
        Example:
            self.press_industry_key('q', after_sleep=0.5)     # 放置管道
            self.press_industry_key('e')                      # 放置传送带
            self.press_industry_key('capslock', after_sleep=1) # 俯瞰模式
        """
        actual_key = self.key_manager.resolve_industry_key(key)
        return self.send_key(actual_key, interval=interval, down_time=down_time, after_sleep=after_sleep)

    def press_combat_key(self, key: str, down_time: float = 0.02, after_sleep: float = 0, interval: int = -1):
        """发送战斗专用部分的游戏热键。
        
        先从配置中查询是否有该键的自定义映射，如果没有则直接使用传入的键值。
        
        Args:
            key: 按键值（如 'e' 等），系统会先检查配置中是否有映射
            down_time: 按键按下持续时间（秒）
            after_sleep: 发送后额外等待时间（秒）
            interval: 按键间隔
            
        Returns:
            send_key 的返回值
            
        Example:
            self.press_combat_key('e', after_sleep=0.5)  # 释放连携技
        """
        actual_key = self.key_manager.resolve_combat_key(key)
        return self.send_key(actual_key, interval=interval, down_time=down_time, after_sleep=after_sleep)

    def move_keys(self, keys, duration):
        """向当前窗口发送按键移动指令
        
        Args:
            keys: 按键或按键列表，例如 "w" 或 ["w", "a"]
            duration: 按键持续时间（秒），例如 0.5
        """
        move_keys(self.hwnd.hwnd, keys, duration)

    def _dodge_with_direction(self, direction_key: str, pre_hold: float = 0.004,
                              dodge_down_time: float = 0.003, after_sleep: float = 0.005):
        """按住方向键后触发闪避键。

        Args:
            direction_key: 方向键，通常为 'w'（前）或 's'（后）
            pre_hold: 方向键预按时长（秒）
            dodge_down_time: 闪避键按下时长（秒）
            after_sleep: 动作结束后等待时长（秒）
        """
        # WASD 移动统一走 move_keys（src/interaction/Key.py）
        # 与闪避键并发执行，保证“同时”触发
        move_thread = threading.Thread(target=self.move_keys, args=(direction_key, pre_hold), daemon=True)
        move_thread.start()
        self.sleep(0.005)
        # 闪避键支持全局热键映射（默认 lshift）
        self.press_key('lshift', down_time=dodge_down_time)
        move_thread.join(timeout=max(pre_hold + 0.002, 0.05))
        if after_sleep > 0:
            self.sleep(after_sleep)

    def dodge_forward(self, pre_hold: float = 0.004, dodge_down_time: float = 0.003, after_sleep: float = 0.005):
        """向前闪避（W + 闪避键）。"""
        self._dodge_with_direction('w', pre_hold=pre_hold, dodge_down_time=dodge_down_time, after_sleep=after_sleep)

    def dodge_backward(self, pre_hold: float = 0.004, dodge_down_time: float = 0.003, after_sleep: float = 0.005):
        """向后闪避（S + 闪避键）。"""
        self._dodge_with_direction('s', pre_hold=pre_hold, dodge_down_time=dodge_down_time, after_sleep=after_sleep)

    def move_to_target_once(self, ocr_obj, max_step=100, min_step=20, slow_radius=200):
        """根据目标位置执行一次视角/鼠标对准
        
        Args:
            ocr_obj: OCR识别到的目标对象
            max_step: 最大移动步长
            min_step: 最小移动步长
            slow_radius: 减速半径
        """
        return move_to_target_once(self.hwnd.hwnd, ocr_obj, self.screen_center, max_step=max_step, min_step=min_step, slow_radius=slow_radius)

    def active_and_send_mouse_delta(self, dx=1, dy=1, activate=True, only_activate=False, delay=0.02, steps=3):
        """激活窗口并发送鼠标位移
        
        Args:
            dx: 水平位移
            dy: 垂直位移
            activate: 是否先激活窗口
            only_activate: 是否仅激活不移动
            delay: 每步延迟
            steps: 分步次数
        """
        return active_and_send_mouse_delta(self.hwnd.hwnd, dx, dy, activate, only_activate, delay, steps)

    def isolate_by_hsv_ranges(self, frame, ranges, invert=True, kernel_size=2):
        """按HSV范围提取颜色区域
        
        Args:
            frame: 输入图像（BGR）
            ranges: HSV区间列表
            invert: 是否反转结果
            kernel_size: 形态学核大小
        """
        return isolate_by_hsv_ranges(frame, ranges, invert, kernel_size)

    def make_hsv_isolator(self, ranges):
        """生成固定HSV范围的图像处理函数
        
        Args:
            ranges: HSV区间列表
        """
        return partial(self.isolate_by_hsv_ranges, ranges=ranges)



    def yolo_detect(
            self,
            name: str | list[str],
            frame=None,
            box: Box | None = None,
            conf: float = 0.25,
    ) -> list[Box]:
        """使用 YOLO 识别目标，并按名称过滤后返回 Box 列表。

        Args:
            name: 目标类别名或名称列表，至少传一个
            frame: 可选，传入待识别帧；不传则使用当前帧
            box: 可选，限制识别区域
            conf: 置信度阈值
        """
        if not name:
            raise ValueError("yolo_detect 至少需要传入一个 name")

        raw_names = [name] if isinstance(name, str) else name
        target_names = {
            str(n.value) if isinstance(n, Enum) else str(n)
            for n in raw_names
            if n is not None
        }
        frame = frame if frame is not None else self.next_frame()
        if frame is None:
            return []

        offset_x = 0
        offset_y = 0
        detect_frame = frame
        if box is not None:
            detect_frame = box.crop_frame(frame)
            offset_x = int(box.x)
            offset_y = int(box.y)

        detections = self.yolo_detector.detect(detect_frame, conf=conf)
        results = [
            det.to_box(offset_x=offset_x, offset_y=offset_y)
            for det in detections
            if det.cls_name in target_names
        ]
        return sorted(results, key=lambda item: item.confidence, reverse=True)

    def click_with_alt(self, x: int| float | Box | List[Box] = -1, y: int|float = -1, move_back: bool = False,
                       name: str | None = None, interval: int = -1, move: bool = True, down_time: float = 0.01,
                       after_sleep: float = 0, key: str = 'left'):
        """按住Alt并点击指定位置
        
        Args:
            x: 点击X坐标（0-1为比例，或像素值）
            y: 点击Y坐标
            move_back: 点击后是否移回原位
            name: 点击目标名称
            interval: 多次点击间隔
            move: 是否移动鼠标到目标
            down_time: 鼠标按下时间
            after_sleep: 点击后等待时间
            key: 鼠标按键('left'/'right'/'middle')
        """
        self.send_key_down("alt")
        self.sleep(0.5)
        self.click(x=x, y=y, move_back=move_back, name=name, interval=interval, move=move, down_time=down_time,
                   after_sleep=after_sleep, key=key)
        self.send_key_up("alt")

    def scroll(self, x: int, y: int, count: int) -> None:
        """在指定像素坐标滚动鼠标滚轮
        
        Args:
            x: 滚动位置X坐标（像素）
            y: 滚动位置Y坐标（像素）
            count: 滚动次数（正数向上，负数向下）
        """
        run_at_window_pos(self.hwnd.hwnd, super().scroll, x, y, 0.5, x, y, count)

    def scroll_relative(self, x: float, y: float, count: int) -> None:
        """在指定比例坐标滚动鼠标滚轮
        
        Args:
            x: 滚动位置X坐标（0-1的比例）
            y: 滚动位置Y坐标（0-1的比例）
            count: 滚动次数
        """
        run_at_window_pos(self.hwnd.hwnd, super().scroll_relative, int(x * self.width), int(y * self.height), 0.5, x, y,
                          count)

    def screen_center(self):
        """获取屏幕中心坐标
        
        Returns:
            tuple: (中心X, 中心Y)
        """
        return int(self.width / 2), int(self.height / 2)

    def wait_ui_stable(
            self,
            method="phash",
            threshold=5,
            stable_time=0.5,
            max_wait=5,
            refresh_interval=0.2,
    ):
        """等待界面稳定（UI停止变化）再执行操作
        
        Args:
            method: 比较两帧相似度方法("phash"/"dhash"/"pixel"/"ssim")
            threshold: 方法对应的阈值
                - phash/dhash: 汉明距离，默认5
                - pixel: 平均像素差，默认5
                - ssim: 相似度(0~1)，默认0.98
            stable_time: 连续稳定时间（秒），默认0.5秒
            max_wait: 最大等待时间（秒），默认5秒
            refresh_interval: 每次获取新帧的间隔（秒），默认0.2秒
        
        Returns:
            bool: True表示UI已稳定，False表示超时仍未稳定
        """
        start_time = time.time()
        last_frame = self.next_frame()  # 获取初始帧
        stable_start = None

        while True:
            current_frame = self.next_frame()  # 获取最新帧

            # 1️⃣ phash / dhash 相似度
            if method in ("phash", "dhash"):
                img1 = Image.fromarray(last_frame)
                img2 = Image.fromarray(current_frame)
                h1 = (
                    imagehash.phash(img1)
                    if method == "phash"
                    else imagehash.dhash(img1)
                )
                h2 = (
                    imagehash.phash(img2)
                    if method == "phash"
                    else imagehash.dhash(img2)
                )
                distance = h1 - h2
                is_stable = distance <= threshold

            # 2️⃣ 像素差法
            elif method == "pixel":
                if last_frame.shape != current_frame.shape:
                    is_stable = False
                else:
                    diff = cv2.absdiff(last_frame, current_frame)
                    is_stable = np.mean(diff) <= threshold

            # 3️⃣ 结构相似度 SSIM
            elif method == "ssim":
                last_gray = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
                current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
                if last_gray.shape != current_gray.shape:
                    is_stable = False
                else:
                    score, _ = ssim(last_gray, current_gray, full=True)
                    is_stable = score >= threshold

            else:
                raise ValueError(f"Unknown method {method}")

            # 处理连续稳定时间
            if is_stable:
                if stable_start is None:
                    stable_start = time.time()
                elif time.time() - stable_start >= stable_time:
                    return True  # 连续稳定达到要求
            else:
                stable_start = None  # 重置计时

            # 超时退出
            if time.time() - start_time > max_wait:
                return False

            last_frame = current_frame
            time.sleep(refresh_interval)

    def align_ocr_or_find_target_to_center(
            self,
            ocr_match_or_feature_name_list,
            only_x=False,
            only_y=False,
            box=None,
            threshold=0.8,
            max_time=50,
            ocr=True,
            use_yolo=False,
            raise_if_fail=True,
            is_num=False,
            need_scroll=False,
            max_step=100,
            min_step=20,
            slow_radius=200,
            once_time=0.5,
            tolerance=TOLERANCE,
            ocr_frame_processor_list=None
    ):
        """将OCR识别或图像特征检测的目标对准屏幕中心（自动移动视角/鼠标）
        
        Args:
            ocr_match_or_feature_name_list: OCR匹配模式(str/List)或特征名称(str/List)
            only_x: True时仅对齐X轴（左右），Y轴保持不变
            only_y: True时仅对齐Y轴（上下），X轴保持不变
            box: 搜索区域框(Box)，None表示全屏。用于限制OCR/特征检测范围
            threshold: 图像特征匹配阈值(0-1)，默认0.8，仅在ocr=False时使用
            max_time: 最大尝试循环次数，默认50次
            ocr: True使用OCR模式识别，False使用图像特征匹配模式
            use_yolo: 在ocr=False时，是否改用YOLO识别（True=YOLO，False=模板特征匹配）
            raise_if_fail: True时对中失败抛出异常，False时返回False
            is_num: 数字型目标Y坐标微调（用于识别数字时的位置校正）
            need_scroll: True时在对中过程中自动滚动（通常用于列表)
            max_step: 单次移动最大步长(像素)
            min_step: 单次移动最小步长(像素)
            slow_radius: 接近目标时减速的半径范围(像素)
            once_time: 每次循环最小耗时(秒)，保证操作频率
            tolerance: 目标中心与屏幕中心的容忍偏差(像素)，默认50，偏差在范围内判定成功
            ocr_frame_processor_list: OCR帧处理函数列表(可用于色彩隔离等预处理)
        
        Returns:
            bool: 成功对中返回True，失败返回False(当raise_if_fail=False时)
        
        Raises:
            Exception: 对中失败且raise_if_fail=True时抛出异常
        """
        if box:
            feature_box = box
        else:
            feature_box = self.box_of_screen(
                (1920 - 1550) / 1920,
                150 / 1080,
                1550 / 1920,
                (1080 - 150) / 1080,
            )
        last_target = None
        last_target_fail_count = 0
        success = False
        random_move_count = 0
        move_count = 0
        scroll_bool = False
        sum_dx = 0
        sum_dy = 0
        for i in range(max_time):
            start_action_time = time.time()
            if ocr:
                # 使用OCR模式识别目标，设置超时时间为2秒，并启用日志记录
                start_time = time.time()
                result = None
                while time.time() - start_time < 1:
                    frame = self.next_frame()
                    if not isinstance(ocr_frame_processor_list, list):
                        ocr_frame_processor_list = [ocr_frame_processor_list]
                    for ocr_frame_processor in ocr_frame_processor_list:
                        result = self.ocr(
                            match=ocr_match_or_feature_name_list,
                            box=box,
                            frame=frame,
                            log=True,
                            frame_processor=ocr_frame_processor,
                        )
                        if result:
                            break
                    if result:
                        break
                    time.sleep(0.1)
            else:
                if isinstance(ocr_match_or_feature_name_list, str):
                    ocr_match_or_feature_name_list = [ocr_match_or_feature_name_list]
                start_time = time.time()
                result = None
                while True:
                    if time.time() - start_time >= 1:
                        break
                    frame = self.next_frame()
                    if use_yolo:
                        result = self.yolo_detect(
                            name=ocr_match_or_feature_name_list,
                            frame=frame,
                            box=feature_box,
                            conf=threshold,
                        )
                    else:
                        for feature_name in ocr_match_or_feature_name_list:
                            if time.time() - start_time >= 1:
                                break

                            result = self.find_feature(
                                feature_name=feature_name,
                                threshold=threshold,
                                box=feature_box,
                            )
                            if result:
                                break
                    if result:
                        break
                    self.sleep(0.1)
            if result:
                success = True
                random_move_count = 0
                move_count = 0
                # OCR 成功
                if isinstance(result, list):
                    result = result[0]
                if is_num:
                    result.y = result.y - int(self.height * ((525 - 486) / 1080))
                if only_y:
                    result.x = self.width // 2 - result.width // 2
                if only_x:
                    result.y = self.height // 2 - result.height // 2
                target_center = (
                    result.x + result.width // 2,
                    result.y + result.height // 2,
                )
                screen_center_pos = self.screen_center()
                last_target = result
                last_target_fail_count = 0
                # 计算偏移量

                dx = target_center[0] - screen_center_pos[0]

                dy = target_center[1] - screen_center_pos[1]

                # 如果目标在容忍范围内
                if abs(dx) <= tolerance and abs(dy) <= tolerance:
                    return True
                else:
                    dx, dy = self.move_to_target_once(result, max_step=max_step, min_step=min_step,
                                                      slow_radius=slow_radius)
                    sum_dx += dx
                    sum_dy += dy

            else:
                # 每次 OCR 失败，直接随机移动
                max_offset = 60  # 最大随机偏移
                if last_target:
                    decay = 0.9 ** last_target_fail_count
                    # 计算目标中心到屏幕中心的偏移

                    screen_center_x, screen_center_y = self.screen_center()
                    offset_x = int((screen_center_x - last_target.x) * decay)
                    offset_y = int((screen_center_y - last_target.y) * decay)
                    offset_width = int(last_target.width / 2 * decay)
                    offset_height = int(last_target.height / 2 * decay)
                    # 直接修改 last_target 坐标
                    last_target.x = screen_center_x - offset_x
                    last_target.y = screen_center_y - offset_y
                    last_target.width = offset_width
                    last_target.height = offset_height
                    dx, dy = self.move_to_target_once(last_target)
                    sum_dx += dx
                    sum_dy += dy
                    last_target_fail_count += 1
                    random_move_count = 0
                    move_count += 1
                    if move_count >= 10:
                        last_target = None
                        move_count = 0
                else:
                    if not success:
                        max_offset = self.width // 4
                    last_target = None
                    last_target_fail_count = 0
                    dx = random.randint(-max_offset, max_offset)
                    if not success:
                        dy = 0
                    else:
                        dy = random.randint(-max_offset, max_offset)

                    # 移动鼠标
                    active_and_send_mouse_delta(
                        self.hwnd.hwnd,
                        dx,
                        dy,
                        activate=True,
                        delay=0.1,
                    )
                    sum_dx += dx
                    sum_dy += dy
                    move_count = 0
                    random_move_count += 1
                    if random_move_count >= 10:
                        success = False
                        random_move_count = 0

            if time.time() - start_action_time < once_time:
                self.sleep(once_time - (time.time() - start_action_time))  # OCR 成功后不需要处理，下一次失败仍然随机
            if not scroll_bool and need_scroll:
                scroll_bool = True
                # cx = int(self.width * 0.5)
                # cy = int(self.height * 0.5)
                for _ in range(6):
                    # self.scroll(cx, cy, 8)
                    pyautogui.scroll(80)
                    self.sleep(1)
        if raise_if_fail:
            raise Exception("对中失败")
        else:
            return False

    def to_model_area(self, area, model):
        """导航到指定区域的特定模块
        
        Args:
            area: 区域名称（如'地区建设'、'仓储'等）
            model: 模块名称（如'仓储节点'、'据点管理'等）
        """
        self.send_key("y", after_sleep=2)
        if not self.wait_click_ocr(
                match="更换", box=self.box.left, time_out=2, after_sleep=2
        ):
            return
        if not self.wait_click_ocr(
                match=re.compile(area),
                box=self.box_of_screen(
                    648 / 1920, 196 / 1080, 648 / 1920 + 628 / 1920, 196 / 1080 + 192 / 1080
                ),
                time_out=2,
                after_sleep=2,
        ):
            return
        if not self.wait_click_ocr(
                match="确认",
                box=self.box.bottom_right,
                time_out=2,
                after_sleep=2,
        ):
            return
        box = self.wait_ocr(
            match=re.compile(f"{model}"), box=self.box.right, time_out=5
        )
        if box:
            self.click(box[0], move_back=True, after_sleep=0.5)
        else:
            self.log_error(f"未找到‘{model}’按钮，任务中止。")
            return

    def skip_dialog(self, end_list=re.compile("确认"), end_box=None):
        """跳过对话框，自动点击"确认"或"跳过"按钮
        
        Args:
            end_list: 结束按钮的OCR匹配模式（默认'确认'）
            end_box: 查找按钮的区域框（默认右下角）
        
        Returns:
            bool: 成功跳过返回True，超时返回False
        """
        if not end_box:
            end_box = self.box.bottom_right
        start_time = time.time()
        while True:
            if time.time() - start_time > 60:
                self.log_info("skip_dialog 超时退出")
                return False
            if self.wait_ocr(match=["工业", "探索"], box=self.box.top_left, time_out=1.5):
                return True
            if self.find_one("skip_dialog_esc", horizontal_variance=0.05):
                self.send_key("esc", after_sleep=0.1)
                start = time.time()
                clicked_confirm = False
                while time.time() - start < 3:
                    confirm = self.find_confirm()
                    if confirm:
                        self.click(confirm, after_sleep=0.4)
                        clicked_confirm = True
                    elif clicked_confirm:
                        self.log_debug("AutoSkipDialogTask no confirm break")
                        return True
            if end_list and self.wait_click_ocr(match=end_list, box=end_box, time_out=0.5):
                return True

    def in_bg(self):
        """判断游戏窗口是否在后台
        
        Returns:
            bool: True表示在后台，False表示在前台
        """
        return not self.hwnd.is_foreground()

    def find_confirm(self):
        """寻找对话框中的"确认"按钮
        
        Returns:
            Box: 找到的按钮位置，否则None
        """
        return self.find_one(
            "skip_dialog_confirm", horizontal_variance=0.05, vertical_variance=0.05
        )

    def in_combat_world(self):
        """判断是否在战斗场景中
        
        Returns:
            bool: True表示在战斗，False表示不在
        """
        in_combat_world = self.find_one("top_left_tab")
        if in_combat_world:
            self._logged_in = True
        return in_combat_world

    def find_f(self):
        """寻找"F"键提示（拾取物品）
        
        Returns:
            Box: 找到的F键提示位置
        """
        return self.find_one("pick_f", vertical_variance=0.05)

    def in_friend_boat(self):
        """判断是否在好友的帝江号舰船中
        
        Returns:
            bool: True表示在舰船中
        """
        return self.wait_ocr(match=re.compile("离开"), box=self.box.top_left)

    def ensure_in_friend_boat(self):
        """确保进入好友帝江号舰船，超时30秒
        
        Returns:
            bool: 成功进入返回True，超时返回False
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > 30:
                self.log_info("进入好友帝江号超时")
                return False
            if self.in_friend_boat():
                return True

    def ensure_main(self, esc=True, time_out=60, after_sleep=2):
        """确保回到主界面（游戏世界），超时会抛出异常
        
        Args:
            esc: 是否按ESC键返回主界面
            time_out: 等待超时时间（秒）
            after_sleep: 完成后等待时间（秒）
        
        Raises:
            Exception: 无法回到主界面时抛出异常
        """
        self.info_set("current task", f"wait main esc={esc}")
        if not self.wait_until(
                lambda: self.is_main(esc=esc), time_out=time_out, raise_if_not_found=False
        ):
            raise Exception("Please start in game world and in team!")
        self.sleep(after_sleep)
        self.info_set("current task", f"in main esc={esc}")

    def in_world(self):
        """判断是否在游戏世界中（非菜单/对话状态）
        
        Returns:
            bool: True表示在世界中
        """
        in_world = self.find_one("esc") and self.find_one("b") and self.find_one("c")
        if in_world:
            self._logged_in = True
        return in_world

    def is_main(self, esc=False):
        """判断是否处于可执行任务的主界面状态
        
        Args:
            esc: 如果是菜单状态，是否按ESC返回（返回False不意味着不是主界面）
        
        Returns:
            bool: True表示处于主界面，False表示需要继续处理
        """
        self.next_frame()  # 确保拿到最新的截图
        if not self._logged_in:
            self.active_and_send_mouse_delta(activate=True, only_activate=True)  # 激活窗口，获取最新状态
        if self.in_world():
            self._logged_in = True
            return True
        if self.wait_login():
            return True
        if result := self.ocr(match=re.compile("结束拜访"), box=self.box.bottom_right):
            self.click(result, after_sleep=1.5)
            return False
        if result := self.ocr(match=[re.compile("确认"), re.compile("确定")], box=self.box.bottom_right):
            self.click(result, after_sleep=1.5)
            return False
        if esc:
            self.back(after_sleep=1.5)
            return False
        return False

    def wait_pop_up(self, after_sleep=0):
        """等待奖励弹窗出现并点击"OK"按钮
        
        Args:
            after_sleep: 点击后等待时间（秒）
        
        Returns:
            bool: 成功点击返回True，超时返回False
        """
        count = 0
        while True:
            if count > 30:
                return False
            result = self.find_one(
                feature_name="reward_ok", box=self.box.bottom, threshold=0.8
            )
            if result:
                self.click(result, after_sleep=after_sleep)
                return True
            self.sleep(1)
            count += 1

    def wait_login(self):
        """处理登录界面的各种弹窗（月卡、签到、奖励等）
        
        Returns:
            bool: 成功处理返回True（进入世界），否则False
        """
        close = None
        if not self._logged_in:
            if self.in_world():
                self._logged_in = True
                return True
            elif self.find_one("monthly_card") or self.find_one("logout"):
                self.click(after_sleep=1)
                return False
            elif close := (
                    self.find_one(
                        "reward_ok",
                        horizontal_variance=0.1,
                        vertical_variance=0.1,
                    )
                    or self.find_one(
                "one_click_claim", horizontal_variance=0.1, vertical_variance=0.1
            )
                    or self.find_one(
                "check_in_close",
                horizontal_variance=0.1,
                vertical_variance=0.1,
                threshold=0.75,
            )
            ):
                self.click(close, after_sleep=1)
                return False
        return False

    def read_essence_info(self) -> EssenceInfo | None:
        """读取当前屏幕中的精华信息（用于装备识别）
        
        Returns:
            EssenceInfo: 精华信息对象，失败返回None
        """
        return read_essence_info(self)
