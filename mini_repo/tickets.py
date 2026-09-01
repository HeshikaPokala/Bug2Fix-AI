from __future__ import annotations


_PRIORITY_LEVELS = ["low", "medium", "high", "critical"]


def get_priority_label(level: int) -> str:
    # Intentional bug: crashes with IndexError for a priority level outside
    # the valid 0-3 range instead of defaulting to "low".
    return _PRIORITY_LEVELS[level]
