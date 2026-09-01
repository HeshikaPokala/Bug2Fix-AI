from __future__ import annotations


def restock_alert(stock_levels: list[int]) -> bool:
    # Intentional bug: crashes when stock_levels is empty instead of treating
    # "no data reported" as "nothing to alert on".
    return min(stock_levels) < 5
