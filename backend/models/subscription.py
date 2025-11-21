from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import date
from typing import Optional
from backend.database import Base


class Subscription(Base):
    """SQLAlchemy Subscription model"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_name = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    frequency = Column(String, nullable=False)  # e.g., "monthly", "yearly"
    start_date = Column(Date, nullable=False)
    next_billing_date = Column(Date, nullable=True)
    status = Column(String, default="active")  # "active" or "cancelled"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User")


# Pydantic schemas
class SubscriptionCreate(BaseModel):
    merchant_name: str
    amount: float
    frequency: str
    start_date: date
    next_billing_date: Optional[date] = None
    status: str = "active"
    user_id: int


class SubscriptionUpdate(BaseModel):
    merchant_name: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    status: Optional[str] = None


class SubscriptionResponse(BaseModel):
    id: int
    merchant_name: str
    amount: float
    frequency: str
    start_date: date
    next_billing_date: Optional[date]
    status: str
    user_id: int
    
    class Config:
        from_attributes = True
