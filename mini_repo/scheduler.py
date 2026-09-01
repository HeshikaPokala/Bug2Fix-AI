from __future__ import annotations

_WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_weekday_name(day_index: int) -> str:
    # Intentional bug: crashes with IndexError when day_index is out of the
    # valid 0-6 range instead of raising a clear validation error.
    return _WEEKDAY_NAMES[day_index]
