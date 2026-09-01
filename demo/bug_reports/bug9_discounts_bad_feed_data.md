Title: Discount calculator crashes on inverted pricing-feed data

Description:
When the upstream pricing feed occasionally sends a sale price higher than the original price (a known data-quality issue on their end), the discount calculation service throws a runtime exception instead of rejecting the bad record.

Expected behavior:
The service should reject records where sale price exceeds original price with a clear validation error, not crash.

Actual behavior:
The service throws an exception and the whole pricing batch job fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.1.0

Reproduction hints:
- Trigger the discount job with a product where `original_price=50.00` and `sale_price=80.00` (feed data error -- sale price above original).
