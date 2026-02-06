"""错题管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models import Mistake, Question, Material
from app.schemas import MistakeResponse, MistakeUpdate

router = APIRouter(prefix="/mistakes", tags=["错题管理"])


@router.get("", response_model=list[MistakeResponse])
def get_mistakes(
    direction_id: int = None,
    mastered: bool = None,
    db: Session = Depends(get_db)
):
    """获取错题列表"""
    query = db.query(Mistake).options(joinedload(Mistake.question))
    
    if direction_id:
        query = (
            query.join(Question)
            .join(Material)
            .filter(Material.direction_id == direction_id)
        )
    
    if mastered is not None:
        query = query.filter(Mistake.mastered == mastered)
    
    return query.order_by(Mistake.created_at.desc()).all()


@router.get("/{mistake_id}", response_model=MistakeResponse)
def get_mistake(mistake_id: int, db: Session = Depends(get_db)):
    """获取错题详情"""
    mistake = (
        db.query(Mistake)
        .options(joinedload(Mistake.question))
        .filter(Mistake.id == mistake_id)
        .first()
    )
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")
    return mistake


@router.patch("/{mistake_id}", response_model=MistakeResponse)
def update_mistake(
    mistake_id: int,
    data: MistakeUpdate,
    db: Session = Depends(get_db)
):
    """更新错题状态"""
    mistake = db.query(Mistake).filter(Mistake.id == mistake_id).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    if data.mastered is not None:
        mistake.mastered = data.mastered
    
    if data.review_count is not None:
        mistake.review_count = data.review_count
    else:
        # 自动增加复习次数
        mistake.review_count += 1
    
    db.commit()
    db.refresh(mistake)
    
    # 重新加载关联
    mistake = (
        db.query(Mistake)
        .options(joinedload(Mistake.question))
        .filter(Mistake.id == mistake_id)
        .first()
    )
    return mistake


@router.delete("/{mistake_id}")
def delete_mistake(mistake_id: int, db: Session = Depends(get_db)):
    """删除错题"""
    mistake = db.query(Mistake).filter(Mistake.id == mistake_id).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    db.delete(mistake)
    db.commit()
    return {"message": "删除成功"}
