"""Helper utilities for ForBill application"""

import re
import random
import string
from datetime import datetime
from typing import Optional


def generate_reference(prefix: str = "FB") -> str:
    """
    Generate a unique transaction reference
    
    Args:
        prefix: Prefix for the reference (e.g., 'FB', 'AIRTIME', 'DATA')
    
    Returns:
        Unique reference string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}_{timestamp}_{random_suffix}"


def validate_phone_number(phone: str) -> Optional[str]:
    """
    Validate and format Nigerian phone number
    
    Args:
        phone: Phone number to validate
    
    Returns:
        Formatted phone number or None if invalid
    """
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check if it starts with country code
    if phone.startswith('234'):
        phone = '0' + phone[3:]
    elif phone.startswith('+234'):
        phone = '0' + phone[4:]
    
    # Validate length and format
    if len(phone) == 11 and phone.startswith('0'):
        return phone
    elif len(phone) == 10:
        return '0' + phone
    
    return None


def format_currency(amount: float) -> str:
    """
    Format amount as Nigerian Naira
    
    Args:
        amount: Amount to format
    
    Returns:
        Formatted currency string
    """
    return f"₦{amount:,.2f}"


def format_phone_display(phone: str) -> str:
    """
    Format phone number for display
    
    Args:
        phone: Phone number to format
    
    Returns:
        Formatted phone number (e.g., 0803 123 4567)
    """
    if len(phone) == 11:
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    return phone


def generate_random_string(length: int = 32) -> str:
    """
    Generate a random string
    
    Args:
        length: Length of string to generate
    
    Returns:
        Random string
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate string to max length
    
    Args:
        text: String to truncate
        max_length: Maximum length
    
    Returns:
        Truncated string
    """
    return text[:max_length] + "..." if len(text) > max_length else text
