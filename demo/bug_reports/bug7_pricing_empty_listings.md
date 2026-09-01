Title: Price range widget crashes for products with no active listings

Description:
When the pricing widget computes the price range for a product with zero active listings, it throws a runtime exception instead of showing "no listings available".

Expected behavior:
The widget should show "no listings available" when the listings list is empty.

Actual behavior:
The widget throws an exception and the product page fails to render.

Environment:
- Python 3.11
- macOS
- Service version: 2.1.0

Reproduction hints:
- Trigger `/products/{id}/price-range` for a product with an empty `prices` list (all listings delisted).
