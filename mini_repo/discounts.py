from __future__ import annotations


def calculate_discount(original_price: float, sale_price: float) -> float:
    # Intentional bug: raises a bare, unhandled ValueError when the sale price
    # is higher than the original price (a pricing-feed data error) instead of
    # rejecting the input cleanly.
    if sale_price > original_price:
        raise ValueError("Sale price cannot exceed original price")
    return (original_price - sale_price) / original_price * 100
