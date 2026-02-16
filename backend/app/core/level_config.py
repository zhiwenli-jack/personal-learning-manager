"""等级与称号配置"""

# 等级经验阈值（累计经验达到阈值即升级）
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 850,
    6: 1300,
    7: 1900,
    8: 2600,
    9: 3450,
    10: 4500,
    11: 5800,
    12: 7400,
    13: 9300,
    14: 11600,
    15: 14400,
}

MAX_LEVEL = max(LEVEL_THRESHOLDS.keys())

# 称号映射（达到对应等级解锁称号）
LEVEL_TITLES = {
    1: "见习探险家",
    3: "初级探险家",
    5: "冒险者",
    8: "资深探险家",
    12: "知识猎人",
    15: "大师探险家",
}


def get_level_for_exp(total_exp: int) -> int:
    """根据累计经验值计算等级"""
    level = 1
    for lv, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if total_exp >= threshold:
            level = lv
    return level


def get_title_for_level(level: int) -> str:
    """根据等级获取称号"""
    title = "见习探险家"
    for lv in sorted(LEVEL_TITLES.keys()):
        if level >= lv:
            title = LEVEL_TITLES[lv]
    return title


def get_next_level_exp(level: int) -> int:
    """获取下一等级所需的累计经验值，已满级返回当前阈值"""
    next_level = level + 1
    if next_level in LEVEL_THRESHOLDS:
        return LEVEL_THRESHOLDS[next_level]
    return LEVEL_THRESHOLDS.get(level, 0)
