from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from ...database import SessionLocal
from ...models.kanban import Column, Task, Label
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class ColumnBase(BaseModel):
    title: str
    order: int = 0

class ColumnCreate(ColumnBase):
    pass

class ColumnResponse(ColumnBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    order: int = 0
    column_id: int

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LabelBase(BaseModel):
    text: str
    color: str

class LabelResponse(LabelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pydantic model para crear etiquetas
class LabelCreate(BaseModel):
    text: str
    color: str

# Pydantic model para enviar múltiples etiquetas
class LabelsRequest(BaseModel):
    labels: List[LabelCreate]

# Endpoints para Columnas
@router.get("/columns", response_model=List[ColumnResponse], tags=["columns"])
def get_columns(db: Session = Depends(get_db)):
    """
    Obtener todas las columnas ordenadas por order
    """
    return db.query(Column).order_by(Column.order).all()

@router.post("/columns", response_model=ColumnResponse, tags=["columns"])
def create_column(column: ColumnCreate, db: Session = Depends(get_db)):
    """
    Crear una nueva columna
    """
    db_column = Column(**column.model_dump())
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    return db_column

@router.put("/columns/{column_id}", response_model=ColumnResponse, tags=["columns"])
def update_column(column_id: int, column: ColumnCreate, db: Session = Depends(get_db)):
    """
    Actualizar una columna existente
    """
    db_column = db.query(Column).filter(Column.id == column_id).first()
    if not db_column:
        raise HTTPException(status_code=404, detail="Column not found")
    
    for key, value in column.model_dump().items():
        setattr(db_column, key, value)
    
    db.commit()
    db.refresh(db_column)
    return db_column

@router.delete("/columns/{column_id}", tags=["columns"])
def delete_column(column_id: int, db: Session = Depends(get_db)):
    """
    Eliminar una columna
    """
    db_column = db.query(Column).filter(Column.id == column_id).first()
    if not db_column:
        raise HTTPException(status_code=404, detail="Column not found")
    
    db.delete(db_column)
    db.commit()
    return {"message": "Column deleted successfully"}

# Endpoints para Tareas
@router.get("/tasks", response_model=List[TaskResponse], tags=["tasks"])
def get_tasks(column_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Obtener todas las tareas, opcionalmente filtradas por column_id
    """
    query = db.query(Task)
    if column_id:
        query = query.filter(Task.column_id == column_id)
    return query.order_by(Task.order).all()

@router.post("/tasks", response_model=TaskResponse, tags=["tasks"])
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """
    Crear una nueva tarea
    """
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    """
    Actualizar una tarea existente
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for key, value in task.model_dump().items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}", tags=["tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Eliminar una tarea
    """
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}

# Endpoints para Etiquetas
@router.get("/labels", response_model=List[LabelResponse], tags=["labels"])
def get_labels(db: Session = Depends(get_db)):
    """
    Obtener todas las etiquetas
    """
    return db.query(Label).all()

@router.get("/tasks/{task_id}/labels", response_model=List[LabelResponse], tags=["tasks"])
def get_task_labels(task_id: int, db: Session = Depends(get_db)):
    """
    Obtener todas las etiquetas de una tarea
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.labels

@router.post("/tasks/{task_id}/labels", response_model=List[LabelResponse], tags=["tasks"])
def add_labels_to_task(task_id: int, labels_request: LabelsRequest, db: Session = Depends(get_db)):
    """
    Actualizar etiquetas de una tarea (reemplaza todas las etiquetas existentes)
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Eliminar todas las etiquetas existentes
    task.labels = []
    
    # Agregar las nuevas etiquetas
    for label_data in labels_request.labels:
        # Verificar si la etiqueta ya existe
        label = db.query(Label).filter(
            Label.text == label_data.text, 
            Label.color == label_data.color
        ).first()
        
        if not label:
            # Crear nueva etiqueta si no existe
            label = Label(text=label_data.text, color=label_data.color)
            db.add(label)
            db.commit()
            db.refresh(label)
        
        # Agregar la etiqueta a la tarea
        task.labels.append(label)
    
    db.commit()
    
    return task.labels 