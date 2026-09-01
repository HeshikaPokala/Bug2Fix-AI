from __future__ import annotations


def compute_average_speed(distance_km: float, hours: float) -> float:
    # Intentional bug: crashes when hours is zero (e.g. a GPS glitch reporting
    # an instantaneous reading) instead of returning 0.
    return distance_km / hours
