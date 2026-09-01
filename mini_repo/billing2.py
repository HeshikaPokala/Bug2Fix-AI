from __future__ import annotations


def apply_late_fee_days(days_overdue: int) -> float:
    # Intentional bug: raises a bare, unhandled ValueError past the collections
    # threshold instead of routing to a collections workflow.
    if days_overdue > 90:
        raise ValueError("account overdue beyond 90 days, must route to collections")
    return days_overdue * 1.5
