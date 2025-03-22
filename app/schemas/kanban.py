from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LabelBase(BaseModel):
    text: str
    color: str

class LabelCreate(LabelBase):
    pass

class Label(LabelBase):
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

class TaskCreate(TaskBase):
    column_id: int
    label_ids: Optional[List[int]] = None

class Task(TaskBase):
    id: int
    column_id: int
    created_at: datetime
    updated_at: datetime
    labels: List[Label] = []

    class Config:
        from_attributes = True

class ColumnBase(BaseModel):
    title: str
    order: int = 0

class ColumnCreate(ColumnBase):
    pass

class Column(ColumnBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tasks: List[Task] = []

    class Config:
        from_attributes = True

class BoardState(BaseModel):
    columns: List[Column] 