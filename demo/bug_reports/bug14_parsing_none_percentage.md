Title: Discount import crashes when percentage field is omitted

Description:
When the promotions feed omits the discount percentage field for a record (sent as null), the import job throws a runtime exception instead of treating it as 0%.

Expected behavior:
The job should treat a missing percentage as 0% instead of crashing.

Actual behavior:
The job throws an exception and the import batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the promotions import job with a record where `percentage=null`.
