from src.tasks.BaseEfTask import BaseEfTask


class PintoTopTask(BaseEfTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "置顶"
        self.description = "置顶游戏"
        self.enable_after_start = True
        self.visible = False
    def run(self):
        self.active_and_send_mouse_delta(only_activate=True)
    