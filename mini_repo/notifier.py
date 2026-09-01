from __future__ import annotations


def format_greeting(name: str) -> str:
    # Intentional bug: crashes when name is None instead of falling back to a
    # generic greeting.
    return "Hello, " + name.upper() + "!"
