import asyncio
from app.services.qwen_service import qwen_service

async def test():
    try:
        print("=" * 50)
        print("1. 测试提炼知识点...")
        content = "Python是一种高级编程语言，具有简洁易读的语法。Python支持面向对象和函数式编程。"
        key_points = await qwen_service.extract_key_points(content, "编程")
        print(f"✅ 知识点提炼成功，共{len(key_points)}个")
        for i, kp in enumerate(key_points, 1):
            print(f"  {i}. {kp['point']}")
        
        print("\n" + "=" * 50)
        print("2. 测试生成题目...")
        questions = await qwen_service.generate_questions(key_points, "编程")
        print(f"✅ 题目生成成功，共{len(questions)}道")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. [{q['type']}] {q['content'][:50]}...")
        
        print("\n" + "=" * 50)
        print("✅ 全部测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
