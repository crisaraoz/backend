# -*- coding: utf-8 -*-
import sys
import os

# Add the root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.kanban import Column, Task, Label
from datetime import datetime

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Create columns
        todo = Column(title="To Do", order=1)
        in_progress = Column(title="In Progress", order=2)
        done = Column(title="Done", order=3)
        
        db.add_all([todo, in_progress, done])
        db.commit()
        
        # Create tasks
        task1 = Task(
            title="Design UI",
            description="Create mockups",
            column_id=todo.id
        )
        
        task2 = Task(
            title="Setup Database",
            description="Configure PostgreSQL",
            column_id=in_progress.id
        )
        
        task3 = Task(
            title="API Development",
            description="Create endpoints",
            column_id=done.id,
            completed=True
        )
        
        db.add_all([task1, task2, task3])
        db.commit()
        
        print("Data inserted successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data() 