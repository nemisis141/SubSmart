from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import date
from backend.database import Base


class Transaction(Base):
    """SQLAlchemy Transaction model"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User")


# Pydantic schemas
class TransactionCreate(BaseModel):
    date: date
    description: str
    amount: float
    user_id: int


class TransactionResponse(BaseModel):
    id: int
    date: date
    description: str
    amount: float
    user_id: int
    
    class Config:
        from_attributes = True
