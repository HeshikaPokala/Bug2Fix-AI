from __future__ import annotations


def average(nums: list[float]) -> float:
    # Intentional bug for assessment: crashes when nums is empty.
    return sum(nums) / len(nums)
