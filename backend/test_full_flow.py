import asyncio
from app.services.qwen_service import qwen_service
from app.models import Question, QuestionType

async def test_full_flow():
    content = "Python是一种解释型、面向对象的高级编程语言，具有动态类型系统和自动内存管理。Python支持多种编程范式。"
    direction = "编程"
    
    try:
        print("=" * 50)
        print("步骤1: 提炼知识点")
        key_points = await qwen_service.extract_key_points(content, direction)
        print(f"✅ 成功提炼 {len(key_points)} 个知识点")
        
        print("\n" + "=" * 50)
        print("步骤2: 生成题目")
        questions_data = await qwen_service.generate_questions(key_points, direction)
        print(f"✅ 成功生成 {len(questions_data)} 道题目")
        
        print("\n" + "=" * 50)
        print("步骤3: 处理题目数据")
        for i, q_data in enumerate(questions_data, 1):
            print(f"\n题目 {i}:")
            print(f"  类型: {q_data.get('type')}")
            print(f"  内容: {q_data.get('content', '')[:50]}...")
            
            # 模拟数据库保存逻辑
            answer = q_data.get("answer", "")
            if isinstance(answer, list):
                answer = ",".join(answer)
            
            try:
                question = Question(
                    material_id=999,  # 测试ID
                    type=QuestionType(q_data.get("type", "single_choice")),
                    difficulty=q_data.get("difficulty", 3),
                    content=q_data.get("content", ""),
                    options=q_data.get("options"),
                    answer=str(answer),
                    explanation=q_data.get("explanation", ""),
                )
                print(f"  ✅ 题目对象创建成功")
            except Exception as e:
                print(f"  ❌ 题目对象创建失败: {e}")
                raise
        
        print("\n" + "=" * 50)
        print("✅ 完整流程测试通过！")
        
    except Exception as e:
        print(f"\n❌ 流程失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_full_flow())
