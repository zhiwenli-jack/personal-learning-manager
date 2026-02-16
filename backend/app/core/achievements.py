"""成就定义配置"""

ACHIEVEMENTS = {
    # === 测验类 ===
    "first_exam": {
        "id": "first_exam",
        "name": "初试身手",
        "description": "完成第一次测验",
        "icon": "target",
        "rarity": "common",
        "exp_reward": 50,
        "category": "exam",
    },
    "exam_master_10": {
        "id": "exam_master_10",
        "name": "勤学不辍",
        "description": "完成10次测验",
        "icon": "scroll",
        "rarity": "rare",
        "exp_reward": 100,
        "category": "exam",
    },
    "perfect_score": {
        "id": "perfect_score",
        "name": "满分学霸",
        "description": "获得一次满分(100分)",
        "icon": "star",
        "rarity": "rare",
        "exp_reward": 100,
        "category": "exam",
    },
    "exam_master_50": {
        "id": "exam_master_50",
        "name": "身经百战",
        "description": "完成50次测验",
        "icon": "trophy",
        "rarity": "epic",
        "exp_reward": 200,
        "category": "exam",
    },

    # === 错题类 ===
    "first_master": {
        "id": "first_master",
        "name": "知错能改",
        "description": "掌握第一道错题",
        "icon": "check",
        "rarity": "common",
        "exp_reward": 50,
        "category": "mistake",
    },
    "mistake_hunter_50": {
        "id": "mistake_hunter_50",
        "name": "错题猎人",
        "description": "掌握50道错题",
        "icon": "medal",
        "rarity": "epic",
        "exp_reward": 200,
        "category": "mistake",
    },

    # === 资料类 ===
    "first_upload": {
        "id": "first_upload",
        "name": "知识收集者",
        "description": "上传第一份学习资料",
        "icon": "book",
        "rarity": "common",
        "exp_reward": 50,
        "category": "material",
    },

    # === 探索类 ===
    "explorer_3_directions": {
        "id": "explorer_3_directions",
        "name": "多面手",
        "description": "探索3个不同的学习方向",
        "icon": "globe",
        "rarity": "rare",
        "exp_reward": 100,
        "category": "explore",
    },
    "full_exploration": {
        "id": "full_exploration",
        "name": "全知之眼",
        "description": "在所有方向达到90%探索率",
        "icon": "eye",
        "rarity": "legendary",
        "exp_reward": 200,
        "category": "explore",
    },

    # === 连续学习类 ===
    "streak_7": {
        "id": "streak_7",
        "name": "七日修行",
        "description": "连续学习7天",
        "icon": "fire",
        "rarity": "rare",
        "exp_reward": 100,
        "category": "streak",
    },
    "streak_30": {
        "id": "streak_30",
        "name": "坚持不懈",
        "description": "连续学习30天",
        "icon": "diamond",
        "rarity": "legendary",
        "exp_reward": 200,
        "category": "streak",
    },
}

# 稀有度经验奖励映射
RARITY_EXP = {
    "common": 50,
    "rare": 100,
    "epic": 200,
    "legendary": 200,
}
