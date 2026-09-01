Title: Catalog import crashes on an overlong SKU

Description:
When the supplier catalog feed includes a SKU longer than 12 characters (a known formatting issue from one supplier), the catalog import job throws a runtime exception instead of rejecting that record.

Expected behavior:
The job should reject an overlong SKU with a clear validation error, not crash the whole batch.

Actual behavior:
The job throws an exception and the catalog import batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the catalog import job with a SKU longer than 12 characters (e.g. `"SUPPLIER-SKU-000123456"`).
