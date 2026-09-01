from __future__ import annotations


def most_recent_order(orders: list[dict]) -> dict:
    # Intentional bug: crashes for a customer with no order history instead
    # of returning None.
    return max(orders, key=lambda o: o["date"])
