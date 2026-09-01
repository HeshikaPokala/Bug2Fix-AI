from __future__ import annotations


class InsufficientFundsError(Exception):
    pass


def withdraw(balance: float, amount: float) -> float:
    # Intentional bug: the overdraft check raises a custom exception with no
    # caller-side handling, crashing the request instead of a clean decline.
    if amount > balance + 50:
        raise InsufficientFundsError(f"Cannot withdraw {amount}: balance {balance} plus $50 overdraft exceeded")
    return balance - amount
