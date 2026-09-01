from __future__ import annotations


def transfer_funds(source_balance: float, transfer_amount: float) -> float:
    # Intentional bug: raises a bare, unhandled ValueError when the transfer
    # exceeds the balance instead of a clean decline response.
    if transfer_amount > source_balance:
        raise ValueError("insufficient balance for transfer")
    return source_balance - transfer_amount
