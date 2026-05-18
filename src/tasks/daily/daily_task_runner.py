from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable

from ok import TaskDisabledException

TaskItem = tuple[str, Callable[[], object]]


def _new_task_status(task_items: Iterable[TaskItem]) -> dict[str, list[str]]:
    return {"success": [], "failed": [], "skipped": [], "all": [key for key, _ in task_items]}


class DailyTaskRunner:
    """DailyTask 的编排执行器。"""

    def __init__(self, task, task_items: Iterable[TaskItem]):
        self.task = task
        self.task_items = list(task_items)
        self.task_status = _new_task_status(self.task_items)
        self.current_task_key: str | None = None
        self.final_summary: dict = {
            "status": "未开始",
            "actual_repeat_total": 0,
            "all_fail_tasks": [],
            "per_round": [],
            "exception": "",
            "current_task": "",
        }
        self._current_round_index: int | None = None
        self._current_repeat_total: int = 0

    def _current_account_info(self) -> dict[str, str]:
        return {
            "account_user": str(getattr(self.task, "current_user", "") or ""),
            "account_id": str(getattr(self.task, "current_account_id", "") or ""),
        }

    def _append_round_summary(self, repeat_idx: int, repeat_total: int):
        account_info = self._current_account_info()
        round_summary = {
            "round": repeat_idx,
            "repeat_total": repeat_total,
            **account_info,
            "success": list(self.task_status.get("success", [])),
            "failed": list(self.task_status.get("failed", [])),
            "skipped": list(self.task_status.get("skipped", [])),
            "all": list(self.task_status.get("all", [])),
        }
        self.final_summary.setdefault("per_round", []).append(round_summary)
        if round_summary["failed"]:
            self.final_summary.setdefault("all_fail_tasks", []).append((repeat_idx, list(round_summary["failed"])))
        return round_summary

    def _mark_round_context(self, repeat_idx: int, repeat_total: int):
        self._current_round_index = repeat_idx
        self._current_repeat_total = repeat_total
        self.final_summary["actual_repeat_total"] = repeat_total

    def _reset_task_status(self):
        self.task_status = _new_task_status(self.task_items)

    def _sync_task_status_info(self):
        info_map = (
            ("failed", "已失败的任务列表"),
            ("success", "已完成的任务列表"),
            ("skipped", "已跳过的任务列表"),
            ("all", "未处理的任务列表"),
        )
        for status_key, info_key in info_map:
            values = self.task_status.get(status_key)
            if values:
                self.task.info_set(info_key, values)
        self._reset_task_status()

    def has_summary_data(self) -> bool:
        return bool(
            self.final_summary.get("per_round")
            or self.final_summary.get("all_fail_tasks")
            or self.final_summary.get("actual_repeat_total", 0) > 0
            or self.final_summary.get("current_task")
        )

    def execute_task(self, key, func):
        self.task_status["all"].remove(key)
        if isinstance(key, str) and not self.task.config.get(key, False):
            self.task_status["skipped"].append(key)
            return True

        self.current_task_key = key
        self.final_summary["current_task"] = key
        self.task.log_info(f"开始任务: {key}")
        self.task.ensure_main()
        result = func()

        if result is False:
            self.task_status["failed"].append(key)
            self.task.screenshot(f'{datetime.now().strftime("%Y%m%d")}_DailyTask_FailTask_{key}')
            self.task.log_info(f"任务 {key} 执行失败", notify=True)
            return False

        self.task_status["success"].append(key)
        self.current_task_key = None
        self.final_summary["current_task"] = ""
        return True

    def run(self, repeat_times: int = 1):
        self.task.log_info("开始执行日常任务...", notify=True)
        self.final_summary["status"] = "运行中"
        self._reset_task_status()
        try:
            for repeat_idx, repeat_total in self.task.iter_multi_account_context(
                repeat_times=repeat_times,
                empty_accounts_message="多账户模式已开启，但账号列表为空，日常任务结束",
                account_log_suffix="任务执行",
            ):
                self._mark_round_context(repeat_idx + 1, repeat_total)
                if not self.task.config.get("多账户模式", False) and self.task.debug:
                    self.task.log_info(f"调试模式，第 {repeat_idx + 1}/{repeat_total} 轮")

                if not self.task._logged_in:
                    self.task.ensure_main(time_out=600)
                else:
                    self.task.ensure_main()
                self.task.log_info(f"开始第 {repeat_idx + 1}/{repeat_total} 轮任务执行")

                for key, func in self.task_items:
                    self.execute_task(key, func)

                if self.task_status["failed"]:
                    self.task.log_info(f"第 {repeat_idx + 1} 轮 | 失败任务: {self.task_status['failed']}", notify=True)
                else:
                    self.task.log_info(f"第 {repeat_idx + 1} 轮 | 日常完成!", notify=True)

                self._append_round_summary(repeat_idx + 1, repeat_total)
                self._sync_task_status_info()

            self.final_summary["status"] = "完成"
            if self.final_summary["actual_repeat_total"] > 1:
                if self.final_summary["all_fail_tasks"]:
                    self.task.log_info(f"执行完成，失败统计: {self.final_summary['all_fail_tasks']}", notify=True)
                else:
                    self.task.log_info("所有任务均成功完成!", notify=True)

            if self.task.config.get("仅退出游戏", False):
                self.final_summary["status"] = "完成后退出"
                self.task.kill_game()
                raise Exception("任务完成，仅退出游戏, 终止其他过程")
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, e: Exception):
        self.final_summary["status"] = "异常结束"
        self.final_summary["exception"] = str(e)
        self.final_summary["current_task"] = self.current_task_key or self.final_summary.get("current_task", "")
        if self._current_round_index is not None:
            already_captured = any(
                round_item.get("round") == self._current_round_index
                and round_item.get("account_id") == self._current_account_info().get("account_id")
                for round_item in self.final_summary.get("per_round", [])
            )
            if not already_captured:
                self._append_round_summary(self._current_round_index, self._current_repeat_total)

        self._sync_task_status_info()
        if self.current_task_key:
            self.task.info_set("当前失败的任务", self.current_task_key)

        try:
            self.task.screenshot(f'{datetime.now().strftime("%Y%m%d")}_DailyTask_Exception')
        except Exception:
            pass

        if not self.task.config.get("发生异常时终止游戏", False):
            self.task.log_info("发生异常，继续游戏", notify=True)
            raise e

        if isinstance(e, TaskDisabledException):
            self.task.log_info("发生异常，继续游戏", notify=True)
            raise e

        self.task.log_info("发生异常，终止游戏", notify=True)
