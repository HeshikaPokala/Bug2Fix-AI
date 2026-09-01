from __future__ import annotations


_MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def get_month_name(month_index: int) -> str:
    # Intentional bug: crashes with IndexError for an out-of-range month index
    # instead of raising a clear validation error.
    return _MONTH_NAMES[month_index]
