from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column as SQLColumn, Integer, DateTime
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = SQLColumn(Integer, primary_key=True, index=True)
    created_at = SQLColumn(DateTime, default=datetime.utcnow)
    updated_at = SQLColumn(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 