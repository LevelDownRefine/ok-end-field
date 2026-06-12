from src.data.FeatureList import FeatureList as fL
from src.tasks.BaseEfTask import BaseEfTask

class DailyDemoMixin(BaseEfTask):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_config.update({
            "⭐演算": True,
        })
        self.config_description.update({
            "⭐演算": "是否执行演武集算任务"
        })

    def battle_demo(self):
        if not self.go_to_DemoGraphic():
            return False
        if not self._demo_click_track_and_transfer():
            return False
        if not self.enter_page():
            return False
        max_time = 3
        for i in range(max_time):
            level = self.read_level()
            if level < 0:
                return False
            refresh_times = 0
            while level <= 5:
                self.wait_click_feature(feature=fL.demo_random_button, time_out=10, raise_if_not_found=False, click_after_delay=0.5)
                self.click_confirm(time_out=2, after_sleep=1)
                refresh_times += 1
                level = self.read_level()
                if level < 0:
                    return False
                if refresh_times == 2 and level >=8:
                    self.log_info("已刷新2次，当前关卡较高，开启双倍奖励")
                    self.wait_click_ocr(match=self.lang.daily_demo_mixin.double_reward, box=self.box_of_screen(0.647, 0.861, 0.738, 0.931), time_out=10, raise_if_not_found=False)
            self.wait_click_feature(feature=fL.start_demo, time_out=10, raise_if_not_found=False, click_after_delay=0.5)
            if not self.wait_click_feature(feature=fL.give_gift, time_out=10, raise_if_not_found=False, click_after_delay=0.5, box=self.box_of_screen(0.944, 0.900, 0.969, 0.941), after_sleep=2):
                self.log_warning("未找到进入战斗按钮")
                return False
            self.ensure_main()
            self.auto_battle()
            if not self.wait_click_feature(feature=fL.restart_battle, vertical_variance=0.1, time_out=10, raise_if_not_found=False):
                self.log_warning("未找到『重新挑战』按钮，可能战斗尚未结束")
                return False
        return True

    def go_to_DemoGraphic(self):
        self.ensure_main()
        self.press_key("f7", after_sleep=2)
        if not self.wait_click_feature(feature=fL.DemoGraphicEnter, time_out=10, raise_if_not_found=False, vertical_variance=0.5):
            self.log_warning("未找到『生息演算』入口，可能没有打开活动入口页")
            return False
        if not self.wait_click_feature(feature=fL.to_max_produce_num, time_out=10, raise_if_not_found=False, box=self.box_of_screen(0.934, 0.881, 0.977, 0.965)):
            self.log_warning("未找到『进入』或最大产出按钮，可能还没进入生息演算列表")
            return False
        return True
    
        
    def _demo_click_track_and_transfer(self):
        """点击『追踪』按钮，进入地图并传送至最近传送点。"""
        if result := self.wait_feature(feature=fL.start_follow, box=self.box.bottom_right, time_out=5, raise_if_not_found=False):
            self.click(result, after_sleep=1)
        else:
            self.log_info("未找到『追踪』按钮，继续尝试自动寻路")
        self.to_near_transfer_point(self.box.bottom_left)
        self.ensure_main()
        self.align_ocr_or_find_target_to_center(ocr_match_or_feature_name_list=fL.demographic_follow, ocr=False)
        if not self.navigate_until_target(target=fL.enter_demo, nav=fL.demographic_follow, target_is_ocr=False, box=self.box_of_screen(0.653, 0.574, 0.679, 0.817)):
            self.log_warning("未能进入『进入演算』目标，可能尚未找到正确路线")
            return False
        return True
        


    def enter_page(self):
        """进入关卡选择界面，等待UI稳定。"""
        result= self.wait_feature(feature=fL.enter_demo, time_out=10, raise_if_not_found=False, box=self.box_of_screen(0.653, 0.574, 0.679, 0.817))
        if not result:
            self.log_warning("未找到『进入演算』按钮，可能还没到关卡入口页")
            return False
        self.click_with_alt(result, after_sleep=1)
        self.wait_ui_stable(refresh_interval=1)
        return True

    def read_level(self):
        start_x = 0.125
        end_x = 0.802
        level_all = 11
        result= self.wait_feature(feature=fL.level_tip, time_out=10, raise_if_not_found=False, box=self.box_of_screen(0.120, 0.724, 0.803, 0.750))
        if not result:
            self.log_warning("未找到等级信息标志，可能没有进入生息演算关卡界面")
            return -1
        leve_x = result.x
        one_level_width = (end_x - start_x) / level_all
        level = int((leve_x - self.screen_width * start_x) / (self.screen_width * one_level_width))
        self.log_info(f"当前等级: {level}")
        return level

