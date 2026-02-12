"""学习资料 API"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Material, MaterialStatus, Direction, Question, QuestionType
from app.schemas import MaterialCreate, MaterialResponse
from app.services import qwen_service
import json
import logging

router = APIRouter(prefix="/materials", tags=["学习资料"])


@router.get("", response_model=list[MaterialResponse])
def get_materials(
    direction_id: int = None,
    db: Session = Depends(get_db)
):
    """获取资料列表"""
    query = db.query(Material)
    if direction_id:
        query = query.filter(Material.direction_id == direction_id)
    return query.order_by(Material.created_at.desc()).all()


async def generate_material_stream(material_id: int, direction_name: str, content: str, db: Session):
    """生成器：流式返回处理进度"""
    try:
        # 1. 提炼知识点
        yield f"data: {json.dumps({'step': 'extracting', 'progress': 10, 'message': '正在提炼知识点...'}, ensure_ascii=False)}\n\n"
        
        material = db.query(Material).filter(Material.id == material_id).first()
        key_points = await qwen_service.extract_key_points(content, direction_name)
        material.key_points = key_points
        db.commit()
        
        yield f"data: {json.dumps({'step': 'extracted', 'progress': 40, 'message': f'知识点提炼完成，共{len(key_points)}个', 'data': key_points}, ensure_ascii=False)}\n\n"
        
        # 2. 生成题目
        yield f"data: {json.dumps({'step': 'generating', 'progress': 50, 'message': '正在生成题目...'}, ensure_ascii=False)}\n\n"
        
        questions_data = await qwen_service.generate_questions(key_points, direction_name)
        
        yield f"data: {json.dumps({'step': 'generated', 'progress': 70, 'message': f'题目生成完成，共{len(questions_data)}道', 'data': len(questions_data)}, ensure_ascii=False)}\n\n"
        
        # 3. 保存题目
        yield f"data: {json.dumps({'step': 'saving', 'progress': 80, 'message': '正在保存题目...'}, ensure_ascii=False)}\n\n"
        
        for i, q_data in enumerate(questions_data):
            answer = q_data.get("answer", "")
            if isinstance(answer, list):
                answer = ",".join(answer)
            
            question = Question(
                material_id=material_id,
                type=QuestionType(q_data.get("type", "single_choice")),
                difficulty=q_data.get("difficulty", 3),
                content=q_data.get("content", ""),
                options=q_data.get("options"),
                answer=str(answer),
                explanation=q_data.get("explanation", ""),
            )
            db.add(question)
            
            progress = 80 + int((i + 1) / len(questions_data) * 15)
            yield f"data: {json.dumps({'step': 'saving', 'progress': progress, 'message': f'保存题目 {i+1}/{len(questions_data)}'}, ensure_ascii=False)}\n\n"
        
        material.status = MaterialStatus.PROCESSED
        db.commit()
        
        yield f"data: {json.dumps({'step': 'completed', 'progress': 100, 'message': '处理完成！', 'material_id': material_id}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            material.status = MaterialStatus.FAILED
            db.commit()
        yield f"data: {json.dumps({'step': 'error', 'progress': 0, 'message': f'处理失败: {str(e)}'}, ensure_ascii=False)}\n\n"


@router.post("", response_model=MaterialResponse)
async def create_material(
    data: MaterialCreate,
    db: Session = Depends(get_db)
):
    """上传资料，立即处理（同步执行）"""
    try:
        # 检查方向是否存在
        direction = db.query(Direction).filter(Direction.id == data.direction_id).first()
        if not direction:
            raise HTTPException(status_code=404, detail="学习方向不存在")
        
        # 检查API密钥是否配置
        if not qwen_service.api_key:
            raise HTTPException(status_code=500, detail="API密钥未配置，请联系管理员设置QWEN_API_KEY")
        
        material = Material(**data.model_dump())
        db.add(material)
        db.commit()
        db.refresh(material)
        
        # 立即同步处理：提炼知识点并生成题目
        direction_name = direction.name if direction else "通用"
        
        # 1. 提炼知识点
        key_points = await qwen_service.extract_key_points(
            material.content, 
            direction_name
        )
        material.key_points = key_points
        
        # 2. 生成题目
        questions_data = await qwen_service.generate_questions(
            key_points,
            direction_name
        )
        
        # 3. 保存题目
        for q_data in questions_data:
            # 处理answer字段：如果是列表，转换为字符串
            answer = q_data.get("answer", "")
            if isinstance(answer, list):
                answer = ",".join(answer)
            
            question = Question(
                material_id=material.id,
                type=QuestionType(q_data.get("type", "single_choice")),
                difficulty=q_data.get("difficulty", 3),
                content=q_data.get("content", ""),
                options=q_data.get("options"),
                answer=str(answer),
                explanation=q_data.get("explanation", ""),
            )
            db.add(question)
        
        material.status = MaterialStatus.PROCESSED
        db.commit()
        db.refresh(material)
        
    except HTTPException:
        # 重新抛出HTTP异常，不需要额外处理
        raise
    except Exception as e:
        # 捕获所有其他异常并记录
        logger = logging.getLogger(__name__)
        logger.error(f"处理资料失败 [ID:{material.id if 'material' in locals() else 'unknown'}]: {str(e)}", exc_info=True)
        print(f"处理资料失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 更新数据库状态
        if 'material' in locals():
            material.status = MaterialStatus.FAILED
            db.commit()
            db.refresh(material)
        else:
            # 如果材料创建失败，可能没有material变量
            raise HTTPException(status_code=500, detail=f"创建资料失败: {str(e)}")
    
    return material


@router.get("/{material_id}/progress")
async def get_material_progress(
    material_id: int,
    db: Session = Depends(get_db)
):
    """获取资料处理进度（SSE流）"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")
    
    # 如果已经处理完成，直接返回
    if material.status != MaterialStatus.PENDING:
        return StreamingResponse(
            iter([f"data: {json.dumps({'step': 'completed', 'progress': 100, 'message': '处理完成！', 'material_id': material_id}, ensure_ascii=False)}\n\n"]),
            media_type="text/event-stream"
        )
    
    # 否则返回流
    return StreamingResponse(
        generate_material_stream(material_id, material.direction.name, material.content, db),
        media_type="text/event-stream"
    )


@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """删除资料及其相关题目"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="资料不存在")
    
    # 删除相关的题目
    db.query(Question).filter(Question.material_id == material_id).delete()
    # 删除资料本身
    db.delete(material)
    db.commit()
    return {"message": "删除成功"}