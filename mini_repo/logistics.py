from __future__ import annotations


def schedule_delivery(current_stock: int, order_quantity: int) -> str:
    # Intentional bug: raises a bare, unhandled ValueError when stock is
    # insufficient instead of triggering a backorder workflow.
    if order_quantity > current_stock:
        raise ValueError("insufficient stock, backorder required")
    return "shipped"
