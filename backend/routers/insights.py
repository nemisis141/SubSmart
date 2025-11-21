from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models.subscription import Subscription
from backend.utils.proration import estimate_annual_savings
from datetime import date, timedelta
from typing import Dict, List

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=dict)
def get_insights(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get subscription insights and analytics
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Dictionary with insights data
    """
    # Get all active subscriptions
    active_subs = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active"
    ).all()
    
    if not active_subs:
        return {
            "total_monthly_cost": 0,
            "total_yearly_cost": 0,
            "subscription_count": 0,
            "highest_spend": None,
            "unused_subscriptions": [],
            "predicted_upcoming_payments": [],
            "category_breakdown": [],
            "spending_trend": []
        }
    
    # Calculate total monthly cost
    total_monthly = 0
    for sub in active_subs:
        if sub.frequency == 'monthly':
            total_monthly += sub.amount
        elif sub.frequency == 'yearly':
            total_monthly += sub.amount / 12
        elif sub.frequency == 'weekly':
            total_monthly += sub.amount * 4.33
        elif sub.frequency == 'bi-weekly':
            total_monthly += sub.amount * 2.17
    
    # Calculate annual savings estimate
    savings_data = estimate_annual_savings([
        {
            'amount': s.amount,
            'frequency': s.frequency
        }
        for s in active_subs
    ])
    
    # Find highest spend subscription
    highest_spend = max(
        active_subs,
        key=lambda s: s.amount if s.frequency == 'monthly' else (
            s.amount / 12 if s.frequency == 'yearly' else s.amount
        )
    )
    
    # Identify unused subscriptions (no recent activity)
    # For demo purposes, mark subscriptions with start_date > 60 days ago as potentially unused
    sixty_days_ago = date.today() - timedelta(days=60)
    unused = [
        {
            "id": sub.id,
            "merchant_name": sub.merchant_name,
            "amount": sub.amount,
            "frequency": sub.frequency,
            "start_date": sub.start_date.isoformat(),
            "reason": "No recent activity detected"
        }
        for sub in active_subs
        if sub.start_date < sixty_days_ago
    ][:3]  # Limit to top 3
    
    # Predict upcoming payments (next 30 days)
    today = date.today()
    thirty_days = today + timedelta(days=30)
    
    upcoming = []
    for sub in active_subs:
        if sub.next_billing_date and today <= sub.next_billing_date <= thirty_days:
            upcoming.append({
                "id": sub.id,
                "merchant_name": sub.merchant_name,
                "amount": sub.amount,
                "billing_date": sub.next_billing_date.isoformat(),
                "days_until": (sub.next_billing_date - today).days
            })
    
    # Sort by date
    upcoming.sort(key=lambda x: x['days_until'])
    
    # Category breakdown (simplified categorization)
    categories = categorize_subscriptions(active_subs)
    
    # Spending trend (mock data for last 6 months)
    spending_trend = generate_spending_trend(active_subs)
    
    return {
        "total_monthly_cost": round(total_monthly, 2),
        "total_yearly_cost": round(savings_data['total_yearly_cost'], 2),
        "subscription_count": len(active_subs),
        "highest_spend": {
            "id": highest_spend.id,
            "merchant_name": highest_spend.merchant_name,
            "amount": highest_spend.amount,
            "frequency": highest_spend.frequency
        },
        "unused_subscriptions": unused,
        "predicted_upcoming_payments": upcoming,
        "category_breakdown": categories,
        "spending_trend": spending_trend,
        "average_per_subscription": round(
            savings_data['average_per_subscription'], 2
        )
    }


def categorize_subscriptions(subscriptions: List[Subscription]) -> List[Dict]:
    """
    Categorize subscriptions by type
    
    Args:
        subscriptions: List of subscriptions
        
    Returns:
        List of category breakdowns
    """
    categories = {
        "Streaming": ["netflix", "spotify", "disney", "hulu", "prime", "youtube"],
        "Productivity": ["microsoft", "adobe", "dropbox", "notion", "slack"],
        "Fitness": ["gym", "peloton", "fitness", "yoga"],
        "News": ["nytimes", "washington", "journal", "news"],
        "Other": []
    }
    
    category_totals = {cat: 0 for cat in categories.keys()}
    
    for sub in subscriptions:
        merchant_lower = sub.merchant_name.lower()
        categorized = False
        
        for category, keywords in categories.items():
            if category == "Other":
                continue
            for keyword in keywords:
                if keyword in merchant_lower:
                    if sub.frequency == 'monthly':
                        category_totals[category] += sub.amount
                    elif sub.frequency == 'yearly':
                        category_totals[category] += sub.amount / 12
                    categorized = True
                    break
            if categorized:
                break
        
        if not categorized:
            if sub.frequency == 'monthly':
                category_totals["Other"] += sub.amount
            elif sub.frequency == 'yearly':
                category_totals["Other"] += sub.amount / 12
    
    return [
        {"category": cat, "amount": round(amount, 2)}
        for cat, amount in category_totals.items()
        if amount > 0
    ]


def generate_spending_trend(subscriptions: List[Subscription]) -> List[Dict]:
    """
    Generate spending trend for last 6 months
    
    Args:
        subscriptions: List of subscriptions
        
    Returns:
        List of monthly spending data
    """
    months = []
    today = date.today()
    
    for i in range(6, 0, -1):
        month_date = today - timedelta(days=30 * i)
        month_name = month_date.strftime("%b %Y")
        
        # Calculate spending for that month
        # For demo, we'll use current total (in real app, would query historical data)
        total = sum(
            sub.amount if sub.frequency == 'monthly' else (
                sub.amount / 12 if sub.frequency == 'yearly' else sub.amount
            )
            for sub in subscriptions
        )
        
        months.append({
            "month": month_name,
            "amount": round(total, 2)
        })
    
    return months
