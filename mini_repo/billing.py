from __future__ import annotations


def get_line_item_price(catalog: dict[str, float], sku: str) -> float:
    # Intentional bug: crashes with KeyError when the sku isn't in the catalog
    # (e.g. a discontinued item still referenced by an old cart) instead of
    # raising a clear domain error.
    return catalog[sku]
