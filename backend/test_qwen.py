import asyncio
from app.services.qwen_service import qwen_service

async def test():
    print('=== 测试题目生成 ===')
    test_points = [
        {'point': 'Python基础', 'description': '解释型语言特点', 'importance': 5},
        {'point': '变量类型', 'description': '动态类型系统', 'importance': 4}
    ]
    try:
        questions = await qwen_service.generate_questions(test_points, '编程')
        print(f'题目生成成功，共{len(questions)}道题')
        for i, q in enumerate(questions, 1):
            qtype = q.get("type", "")
            qcontent = q.get("content", "")
            print(f'{i}. [{qtype}] {qcontent}')
    except Exception as e:
        print('题目生成失败:', str(e))
        import traceback
        traceback.print_exc()

asyncio.run(test())
