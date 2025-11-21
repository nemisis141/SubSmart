from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.subscription import (
    Subscription, 
    SubscriptionCreate, 
    SubscriptionUpdate,
    SubscriptionResponse
)
from backend.models.transaction import Transaction
from backend.utils.detect_recurring import detect_recurring_subscriptions
from backend.utils.proration import calculate_proration
from typing import List
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class ProrationRequest(BaseModel):
    cancellation_date: date


@router.get("", response_model=List[SubscriptionResponse])
def get_subscriptions(
    user_id: int = 1,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Get all subscriptions for a user
    
    Args:
        user_id: User ID
        status: Filter by status (active/cancelled)
        db: Database session
        
    Returns:
        List of subscriptions
    """
    query = db.query(Subscription).filter(Subscription.user_id == user_id)
    
    if status:
        query = query.filter(Subscription.status == status)
    
    subscriptions = query.all()
    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db)
):
    """
    Get subscription details by ID
    
    Args:
        subscription_id: Subscription ID
        db: Database session
        
    Returns:
        Subscription details
    """
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription


@router.post("/detect", response_model=dict)
def detect_subscriptions(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Detect recurring subscriptions from transactions
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Dictionary with detection results
    """
    # Get all transactions for user
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if not transactions:
        raise HTTPException(
            status_code=404, 
            detail="No transactions found for user"
        )
    
    # Convert to list of dicts for algorithm
    txn_list = [
        {
            'date': t.date,
            'description': t.description,
            'amount': t.amount
        }
        for t in transactions
    ]
    
    # Detect recurring patterns
    detected = detect_recurring_subscriptions(txn_list)
    
    # Store detected subscriptions
    created_count = 0
    for sub_data in detected:
        # Check if subscription already exists
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.merchant_name == sub_data['merchant_name']
        ).first()
        
        if not existing:
            subscription = Subscription(
                merchant_name=sub_data['merchant_name'],
                amount=sub_data['amount'],
                frequency=sub_data['frequency'],
                start_date=sub_data['start_date'],
                next_billing_date=sub_data.get('next_billing_date'),
                status=sub_data['status'],
                user_id=user_id
            )
            db.add(subscription)
            created_count += 1
    
    db.commit()
    
    return {
        "status": "success",
        "detected_count": len(detected),
        "created_count": created_count,
        "subscriptions": detected
    }


@router.post("/{subscription_id}/prorate", response_model=dict)
def calculate_subscription_proration(
    subscription_id: int,
    request: ProrationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate proration refund for a subscription
    
    Args:
        subscription_id: Subscription ID
        request: Proration request with cancellation date
        db: Database session
        
    Returns:
        Proration calculation details
    """
    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Calculate proration
    result = calculate_proration(
        amount=subscription.amount,
        frequency=subscription.frequency,
        last_renewal_date=subscription.start_date,
        cancellation_date=request.cancellation_date
    )
    
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.post("", response_model=SubscriptionResponse)
def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """
    Manually create a subscription
    
    Args:
        subscription: Subscription data
        db: Database session
        
    Returns:
        Created subscription
    """
    db_subscription = Subscription(**subscription.dict())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    subscription_update: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a subscription
    
    Args:
        subscription_id: Subscription ID
        subscription_update: Updated fields
        db: Database session
        
    Returns:
        Updated subscription
    """
    db_subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Update fields
    update_data = subscription_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_subscription, field, value)
    
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


@router.delete("/{subscription_id}")
def delete_subscription(
    subscription_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a subscription
    
    Args:
        subscription_id: Subscription ID
        db: Database session
        
    Returns:
        Success message
    """
    db_subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id
    ).first()
    
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    db.delete(db_subscription)
    db.commit()
    
    return {"status": "success", "message": "Subscription deleted"}
