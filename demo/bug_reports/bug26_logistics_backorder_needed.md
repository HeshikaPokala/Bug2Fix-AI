Title: Delivery scheduling crashes when order exceeds current stock

Description:
When an order quantity exceeds the current warehouse stock, the delivery-scheduling service throws a runtime exception instead of triggering a backorder workflow.

Expected behavior:
The endpoint should trigger a backorder workflow when stock is insufficient, not crash.

Actual behavior:
The endpoint throws an exception and the delivery scheduling request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/logistics/schedule` for a warehouse with `current_stock=8` and an `order_quantity=25`.
