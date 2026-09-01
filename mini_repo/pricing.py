from __future__ import annotations


def price_range(prices: list[float]) -> float:
    # Intentional bug: crashes when prices is empty instead of treating "no
    # listings" as a zero range.
    return max(prices) - min(prices)
