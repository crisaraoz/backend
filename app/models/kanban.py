from sqlalchemy import Column as SQLColumn, String, Integer, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from .base import BaseModel, Base

# Tabla de relación muchos a muchos entre Task y Label
task_labels = Table(
    'task_labels',
    Base.metadata,
    SQLColumn('task_id', Integer, ForeignKey('tasks.id')),
    SQLColumn('label_id', Integer, ForeignKey('labels.id'))
)

class Column(BaseModel):
    __tablename__ = "columns"

    title = SQLColumn(String, nullable=False)
    order = SQLColumn(Integer, default=0)
    
    # Relaciones
    tasks = relationship("Task", back_populates="column", cascade="all, delete-orphan")

class Task(BaseModel):
    __tablename__ = "tasks"

    title = SQLColumn(String, nullable=False)
    description = SQLColumn(String)
    completed = SQLColumn(Boolean, default=False)
    order = SQLColumn(Integer, default=0)
    column_id = SQLColumn(Integer, ForeignKey("columns.id"))

    # Relaciones
    column = relationship("Column", back_populates="tasks")
    labels = relationship("Label", secondary=task_labels, back_populates="tasks")

class Label(BaseModel):
    __tablename__ = "labels"

    text = SQLColumn(String, nullable=False)
    color = SQLColumn(String, nullable=False)
    
    # Relaciones
    tasks = relationship("Task", secondary=task_labels, back_populates="labels") 