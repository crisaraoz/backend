from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.kanban import Column as ColumnModel, Task as TaskModel, Label as LabelModel
from ..schemas.kanban import ColumnCreate, TaskCreate, LabelCreate

# Column operations
def get_columns(db: Session) -> List[ColumnModel]:
    return db.query(ColumnModel).order_by(ColumnModel.order).all()

def create_column(db: Session, column: ColumnCreate) -> ColumnModel:
    db_column = ColumnModel(**column.model_dump())
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    return db_column

def update_column(db: Session, column_id: int, title: str) -> Optional[ColumnModel]:
    db_column = db.query(ColumnModel).filter(ColumnModel.id == column_id).first()
    if db_column:
        db_column.title = title
        db.commit()
        db.refresh(db_column)
    return db_column

def delete_column(db: Session, column_id: int) -> bool:
    db_column = db.query(ColumnModel).filter(ColumnModel.id == column_id).first()
    if db_column:
        db.delete(db_column)
        db.commit()
        return True
    return False

# Task operations
def create_task(db: Session, task: TaskCreate) -> TaskModel:
    label_ids = task.label_ids or []
    task_data = task.model_dump(exclude={'label_ids'})
    
    db_task = TaskModel(**task_data)
    if label_ids:
        db_labels = db.query(LabelModel).filter(LabelModel.id.in_(label_ids)).all()
        db_task.labels = db_labels
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(
    db: Session,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
    column_id: Optional[int] = None,
    label_ids: Optional[List[int]] = None
) -> Optional[TaskModel]:
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if db_task:
        if title is not None:
            db_task.title = title
        if description is not None:
            db_task.description = description
        if completed is not None:
            db_task.completed = completed
        if column_id is not None:
            db_task.column_id = column_id
        if label_ids is not None:
            db_labels = db.query(LabelModel).filter(LabelModel.id.in_(label_ids)).all()
            db_task.labels = db_labels
        
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int) -> bool:
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

# Label operations
def create_label(db: Session, label: LabelCreate) -> LabelModel:
    db_label = LabelModel(**label.model_dump())
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label

def get_labels(db: Session) -> List[LabelModel]:
    return db.query(LabelModel).all()

def update_label(db: Session, label_id: int, text: str, color: str) -> Optional[LabelModel]:
    db_label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    if db_label:
        db_label.text = text
        db_label.color = color
        db.commit()
        db.refresh(db_label)
    return db_label

def delete_label(db: Session, label_id: int) -> bool:
    db_label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    if db_label:
        db.delete(db_label)
        db.commit()
        return True
    return False 