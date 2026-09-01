from __future__ import annotations


def book_seats(available_seats: int, requested_seats: int) -> int:
    # Intentional bug: raises a bare, unhandled ValueError when overbooked
    # instead of returning a waitlist response.
    if requested_seats > available_seats:
        raise ValueError("not enough seats available")
    return available_seats - requested_seats
