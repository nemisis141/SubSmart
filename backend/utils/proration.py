from datetime import date, timedelta
from typing import Dict


def calculate_proration(
    amount: float,
    frequency: str,
    last_renewal_date: date,
    cancellation_date: date
) -> Dict[str, any]:
    """
    Calculate proration refund for a cancelled subscription
    
    Formula:
    - daily_cost = amount / billing_cycle_days
    - used_days = cancellation_date - last_renewal_date
    - refund = amount - (daily_cost * used_days)
    
    Args:
        amount: Subscription amount
        frequency: Billing frequency (monthly, yearly, weekly, bi-weekly)
        last_renewal_date: Date of last billing
        cancellation_date: Date of cancellation
        
    Returns:
        Dictionary with proration details
    """
    # Determine billing cycle days
    billing_cycle_days = get_billing_cycle_days(frequency)
    
    if billing_cycle_days is None:
        return {
            'error': f'Unknown frequency: {frequency}',
            'refund': 0.0
        }
    
    # Calculate used days
    used_days = (cancellation_date - last_renewal_date).days
    
    # Ensure used_days is not negative
    if used_days < 0:
        return {
            'error': 'Cancellation date is before last renewal date',
            'refund': 0.0
        }
    
    # Ensure used_days doesn't exceed billing cycle
    if used_days > billing_cycle_days:
        used_days = billing_cycle_days
    
    # Calculate daily cost
    daily_cost = amount / billing_cycle_days
    
    # Calculate used amount
    used_amount = daily_cost * used_days
    
    # Calculate refund
    refund = amount - used_amount
    
    # Ensure refund is not negative
    refund = max(0.0, refund)
    
    # Calculate next billing date (if not cancelled)
    next_billing_date = last_renewal_date + timedelta(days=billing_cycle_days)
    
    # Calculate remaining days
    remaining_days = billing_cycle_days - used_days
    
    return {
        'amount': round(amount, 2),
        'frequency': frequency,
        'billing_cycle_days': billing_cycle_days,
        'last_renewal_date': last_renewal_date.isoformat(),
        'cancellation_date': cancellation_date.isoformat(),
        'next_billing_date': next_billing_date.isoformat(),
        'used_days': used_days,
        'remaining_days': remaining_days,
        'daily_cost': round(daily_cost, 2),
        'used_amount': round(used_amount, 2),
        'refund': round(refund, 2),
        'refund_percentage': round((refund / amount) * 100, 1) if amount > 0 else 0
    }


def get_billing_cycle_days(frequency: str) -> int:
    """
    Get number of days in billing cycle based on frequency
    
    Args:
        frequency: Billing frequency
        
    Returns:
        Number of days in billing cycle
    """
    frequency_map = {
        'weekly': 7,
        'bi-weekly': 14,
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365,
        'annual': 365
    }
    
    return frequency_map.get(frequency.lower())


def estimate_annual_savings(subscriptions: list) -> Dict[str, any]:
    """
    Estimate potential annual savings from cancelling subscriptions
    
    Args:
        subscriptions: List of subscription dictionaries
        
    Returns:
        Dictionary with savings estimates
    """
    total_monthly = 0.0
    total_yearly = 0.0
    
    for sub in subscriptions:
        amount = sub.get('amount', 0)
        frequency = sub.get('frequency', 'monthly').lower()
        
        if frequency == 'monthly':
            total_monthly += amount
            total_yearly += amount * 12
        elif frequency == 'yearly' or frequency == 'annual':
            total_yearly += amount
            total_monthly += amount / 12
        elif frequency == 'weekly':
            total_yearly += amount * 52
            total_monthly += amount * 4.33
        elif frequency == 'bi-weekly':
            total_yearly += amount * 26
            total_monthly += amount * 2.17
    
    return {
        'total_monthly_cost': round(total_monthly, 2),
        'total_yearly_cost': round(total_yearly, 2),
        'average_per_subscription': round(total_monthly / len(subscriptions), 2) if subscriptions else 0
    }
