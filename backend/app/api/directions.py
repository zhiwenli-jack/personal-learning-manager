"""学习方向 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Direction
from app.schemas import DirectionCreate, DirectionResponse

router = APIRouter(prefix="/directions", tags=["学习方向"])


@router.get("", response_model=list[DirectionResponse])
def get_directions(db: Session = Depends(get_db)):
    """获取所有学习方向"""
    return db.query(Direction).all()


@router.post("", response_model=DirectionResponse)
def create_direction(data: DirectionCreate, db: Session = Depends(get_db)):
    """创建学习方向"""
    # 检查是否已存在
    existing = db.query(Direction).filter(Direction.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="该学习方向已存在")
    
    direction = Direction(**data.model_dump())
    db.add(direction)
    db.commit()
    db.refresh(direction)
    return direction


@router.get("/{direction_id}", response_model=DirectionResponse)
def get_direction(direction_id: int, db: Session = Depends(get_db)):
    """获取学习方向详情"""
    direction = db.query(Direction).filter(Direction.id == direction_id).first()
    if not direction:
        raise HTTPException(status_code=404, detail="学习方向不存在")
    return direction


@router.delete("/{direction_id}")
def delete_direction(direction_id: int, db: Session = Depends(get_db)):
    """删除学习方向"""
    direction = db.query(Direction).filter(Direction.id == direction_id).first()
    if not direction:
        raise HTTPException(status_code=404, detail="学习方向不存在")
    
    db.delete(direction)
    db.commit()
    return {"message": "删除成功"}
