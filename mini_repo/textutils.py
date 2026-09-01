from __future__ import annotations


def uppercase_first_letter(word: str) -> str:
    # Intentional bug: crashes on an empty string instead of returning it
    # unchanged.
    return word[0].upper() + word[1:]
