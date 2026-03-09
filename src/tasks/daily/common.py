import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ok import Box


def build_name_patterns(find_name: str):
    if len(find_name) >= 2:
        keys = [find_name[i:i + 2] for i in range(len(find_name) - 1)]
    else:
        keys = [find_name]

    return [re.compile(k) for k in keys]


class LiaisonResult(int, Enum):
    """前往联络站流程的结果枚举。"""

    SUCCESS = 1
    FAIL = 2
    FIND_CHAT_ICON = 3


@dataclass
class GoodsInfo:
    """单个货物的识别与价格信息。"""

    good_name: str
    good_price: int
    friend_price: Optional[int]
    stock_quantity: int
    name_box: "Box"
    friend_name_box: Optional["Box"]
