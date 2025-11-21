from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, EmailStr
from backend.database import Base


class User(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)


# Pydantic schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    
    class Config:
        from_attributes = True
