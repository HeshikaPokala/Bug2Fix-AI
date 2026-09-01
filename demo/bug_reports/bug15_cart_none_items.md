Title: Checkout total crashes for expired cart sessions

Description:
When a checkout request arrives for a session whose cart expired server-side (items resolves to null), the checkout service throws a runtime exception instead of treating it as an empty cart.

Expected behavior:
The endpoint should treat a null cart as empty (total $0) instead of crashing.

Actual behavior:
The endpoint throws an exception and checkout fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/checkout/total` for a session whose cart items resolve to null.
