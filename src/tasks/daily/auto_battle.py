"""自动战斗模块 - 从 AutoCombatTask 复用战斗逻辑"""
import time
from typing import TYPE_CHECKING, Callable

from src.tasks.AutoCombatTask import AutoCombatLogic

if TYPE_CHECKING:
    from src.tasks.BaseEfTask import BaseEfTask


def auto_battle(task_instance: "BaseEfTask", config: dict = None,
                end_check: Callable[["BaseEfTask"], bool] | None = None) -> bool:
    """
    执行完整的自动战斗流程，持续监控并自动战斗直到退出。
    
    Args:
        task_instance: BaseEfTask 实例（通常是 DailyTask）
        config: 战斗配置字典，包含：
            - "技能释放": 技能序列字符串（如"123"）
            - "启动技能点数": 触发技能的点数阈值（1-3）
            - "后台结束战斗通知": 是否在后台时通知战斗结束
        end_check: 自定义结束判定函数，返回 True 表示应退出战斗
    
    Returns:
        bool: 战斗是否完成
    """
    if config is None:
        config = {
            "技能释放": "123",
            "启动技能点数": 2,
            "后台结束战斗通知": True,
            "平A间隔": 0.12,
            "无数字操作间隔": 6,
        }
    
    # 直接调用独立的自动战斗逻辑
    return AutoCombatLogic(task_instance).run()
