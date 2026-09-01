Title: Recommendations service crashes for first-time customers

Description:
When the recommendations service tries to find a new customer's most recent order to personalize suggestions, it throws a runtime exception for customers with zero order history.

Expected behavior:
The service should return no personalization (not crash) for a customer with no orders.

Actual behavior:
The service throws an exception and the recommendations widget fails to load.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/recommendations/personalize` for a customer with an empty `orders` list.
