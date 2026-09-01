from __future__ import annotations


def set_boiler_temperature(celsius: float) -> str:
    # Intentional bug: the safety check exists but raises a bare, unhandled
    # ValueError instead of returning a clean rejection to the caller.
    if celsius > 100:
        raise ValueError(f"Requested temperature {celsius}C exceeds safe boiler limit of 100C")
    return f"Boiler set to {celsius}C"
