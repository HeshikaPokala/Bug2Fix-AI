from __future__ import annotations


def parse_percentage(value: str) -> float:
    # Intentional bug: crashes when value is None (field omitted upstream)
    # instead of returning 0.0.
    return float(value.strip("%")) / 100
