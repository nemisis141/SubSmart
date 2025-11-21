import re
from datetime import timedelta
from typing import List, Dict
from collections import defaultdict


def normalize_merchant(description: str) -> str:
    """
    Normalize merchant name for matching
    
    Args:
        description: Raw transaction description
        
    Returns:
        Normalized merchant name
    """
    # Convert to lowercase
    normalized = description.lower()
    
    # Remove common patterns
    patterns = [
        r'\d{2}/\d{2}',  # Dates
        r'#\d+',  # Reference numbers
        r'\*+\d+',  # Card numbers
        r'ref\s*:?\s*\w+',  # Reference codes
    ]
    
    for pattern in patterns:
        normalized = re.sub(pattern, '', normalized)
    
    # Remove special characters except spaces
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    # Extract core merchant name (first 2-3 words typically)
    words = normalized.split()
    if len(words) > 3:
        normalized = ' '.join(words[:3])
    
    return normalized.strip()


def detect_recurring_subscriptions(transactions: List[Dict]) -> List[Dict]:
    """
    Detect recurring subscriptions from transaction list
    
    Args:
        transactions: List of transaction dictionaries with date, description, amount
        
    Returns:
        List of detected subscription dictionaries
    """
    # Group transactions by normalized merchant name
    merchant_groups = defaultdict(list)
    
    for transaction in transactions:
        merchant = normalize_merchant(transaction['description'])
        if merchant:
            merchant_groups[merchant].append(transaction)
    
    subscriptions = []
    
    for merchant, txns in merchant_groups.items():
        # Need at least 2 transactions to detect pattern
        if len(txns) < 2:
            continue
        
        # Sort by date
        txns_sorted = sorted(txns, key=lambda x: x['date'])
        
        # Check for recurring pattern
        is_recurring, frequency = check_recurring_pattern(txns_sorted)
        
        if is_recurring:
            # Calculate next billing date
            last_txn = txns_sorted[-1]
            
            if frequency == 'monthly':
                # Estimate next billing (30 days from last)
                next_billing = last_txn['date'] + timedelta(days=30)
            elif frequency == 'yearly':
                next_billing = last_txn['date'] + timedelta(days=365)
            else:
                next_billing = None
            
            # Get most recent amount (handle slight variations)
            recent_amounts = [t['amount'] for t in txns_sorted[-3:]]
            avg_amount = sum(recent_amounts) / len(recent_amounts)
            
            subscriptions.append({
                'merchant_name': merchant.title(),
                'amount': round(avg_amount, 2),
                'frequency': frequency,
                'start_date': txns_sorted[0]['date'],
                'next_billing_date': next_billing,
                'status': 'active',
                'transaction_count': len(txns_sorted)
            })
    
    return subscriptions


def check_recurring_pattern(transactions: List[Dict]) -> tuple[bool, str]:
    """
    Check if transactions show recurring pattern
    
    Args:
        transactions: Sorted list of transactions
        
    Returns:
        Tuple of (is_recurring, frequency)
    """
    if len(transactions) < 2:
        return False, None
    
    # Calculate gaps between transactions
    gaps = []
    for i in range(1, len(transactions)):
        gap = (transactions[i]['date'] - transactions[i-1]['date']).days
        gaps.append(gap)
    
    # Check for monthly pattern (28-35 days, allowing for variation)
    monthly_gaps = [g for g in gaps if 25 <= g <= 35]
    if len(monthly_gaps) >= len(gaps) * 0.7:  # 70% of gaps are monthly
        return True, 'monthly'
    
    # Check for yearly pattern (350-380 days)
    yearly_gaps = [g for g in gaps if 350 <= g <= 380]
    if len(yearly_gaps) >= len(gaps) * 0.7:
        return True, 'yearly'
    
    # Check for weekly pattern (6-8 days)
    weekly_gaps = [g for g in gaps if 6 <= g <= 8]
    if len(weekly_gaps) >= len(gaps) * 0.7:
        return True, 'weekly'
    
    # Check for bi-weekly pattern (13-15 days)
    biweekly_gaps = [g for g in gaps if 13 <= g <= 15]
    if len(biweekly_gaps) >= len(gaps) * 0.7:
        return True, 'bi-weekly'
    
    return False, None
