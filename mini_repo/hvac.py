from __future__ import annotations


def set_fan_speed(percent: int) -> str:
    # Intentional bug: raises a bare, unhandled ValueError above 100% instead
    # of rejecting the request cleanly.
    if percent > 100:
        raise ValueError(f"Fan speed {percent}% exceeds maximum of 100%")
    return f"Fan set to {percent}%"
