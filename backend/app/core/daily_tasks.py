"""每日任务定义配置"""

DAILY_TASKS = {
    "daily_exam": {
        "id": "daily_exam",
        "name": "每日挑战",
        "description": "完成1次测验",
        "icon": "scroll",
        "target": 1,
        "exp_reward": 30,
        "task_type": "exam",
    },
    "daily_perfect": {
        "id": "daily_perfect",
        "name": "追求完美",
        "description": "获得一次80分以上成绩",
        "icon": "star",
        "target": 1,
        "exp_reward": 50,
        "task_type": "exam_score",
    },
    "daily_mistakes": {
        "id": "daily_mistakes",
        "name": "错题复习",
        "description": "掌握3道错题",
        "icon": "check",
        "target": 3,
        "exp_reward": 40,
        "task_type": "mistake",
    },
    "daily_material": {
        "id": "daily_material",
        "name": "知识积累",
        "description": "上传1份学习资料",
        "icon": "book",
        "target": 1,
        "exp_reward": 30,
        "task_type": "material",
    },
    "daily_questions": {
        "id": "daily_questions",
        "name": "题海战术",
        "description": "答对10道题目",
        "icon": "target",
        "target": 10,
        "exp_reward": 40,
        "task_type": "questions",
    },
}

# 每日从任务池中随机选取的任务数
DAILY_TASK_COUNT = 3
