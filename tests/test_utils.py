"""Test helper utilities"""

from app.utils.helpers import (
    validate_phone_number,
    format_currency,
    generate_reference,
    format_phone_display
)


def test_validate_phone_number():
    """Test phone number validation"""
    # Valid formats
    assert validate_phone_number("08012345678") == "08012345678"
    assert validate_phone_number("2348012345678") == "08012345678"
    assert validate_phone_number("+2348012345678") == "08012345678"
    assert validate_phone_number("8012345678") == "08012345678"
    
    # Invalid formats
    assert validate_phone_number("123") is None
    assert validate_phone_number("abcdefghijk") is None


def test_format_currency():
    """Test currency formatting"""
    assert format_currency(1000) == "₦1,000.00"
    assert format_currency(500.50) == "₦500.50"
    assert format_currency(0) == "₦0.00"


def test_generate_reference():
    """Test reference generation"""
    ref = generate_reference("TEST")
    assert ref.startswith("TEST_")
    assert len(ref) > 10


def test_format_phone_display():
    """Test phone display formatting"""
    assert format_phone_display("08012345678") == "0801 234 5678"
