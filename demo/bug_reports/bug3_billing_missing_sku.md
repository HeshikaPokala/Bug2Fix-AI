Title: Checkout crashes when cart references a discontinued SKU

Description:
When a customer's cart contains a SKU that has since been removed from the catalog, the checkout service throws a runtime exception and returns HTTP 500 instead of flagging the item as unavailable.

Expected behavior:
The endpoint should return a clear "item unavailable" response for SKUs not present in the catalog.

Actual behavior:
The endpoint throws an exception and checkout fails entirely, even for the other valid items in the cart.

Environment:
- Python 3.11
- macOS
- Service version: 2.0.1

Reproduction hints:
- Trigger `/checkout` with a cart containing SKU `"disc-2026-legacy"`, which was removed from the catalog last week.
