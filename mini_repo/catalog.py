from __future__ import annotations


def validate_product_sku(sku: str) -> str:
    # Intentional bug: raises a bare, unhandled ValueError for an overlong SKU
    # instead of rejecting the catalog entry cleanly.
    if len(sku) > 12:
        raise ValueError("sku exceeds maximum length of 12")
    return sku
