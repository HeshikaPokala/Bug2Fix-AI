from __future__ import annotations


def divide_shares(total: float, shareholders: int) -> float:
    # Intentional bug: crashes when shareholders is zero (a data-migration
    # edge case) instead of returning 0.
    return total / shareholders
