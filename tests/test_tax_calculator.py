"""
Tests for tax_calculator module
"""

import pytest
from src.tax_calculator import calculate_price_excl_tax


def test_calculate_price_excl_tax_basic():
    """Test basic tax calculation"""
    assert calculate_price_excl_tax(35200) == 32000
    assert calculate_price_excl_tax(8800) == 8000
    assert calculate_price_excl_tax(11000) == 10000


def test_calculate_price_excl_tax_edge_cases():
    """Test edge cases"""
    assert calculate_price_excl_tax(0) == 0
    assert calculate_price_excl_tax(1.1) == 1
    assert calculate_price_excl_tax(10) == 9


def test_calculate_price_excl_tax_negative():
    """Test that negative prices raise ValueError"""
    with pytest.raises(ValueError):
        calculate_price_excl_tax(-100)
