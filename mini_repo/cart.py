from __future__ import annotations


def total_cart_value(items: list[dict]) -> float:
    # Intentional bug: crashes when items is None (session expired mid-checkout)
    # instead of treating it as an empty cart.
    return sum(item["price"] for item in items)
