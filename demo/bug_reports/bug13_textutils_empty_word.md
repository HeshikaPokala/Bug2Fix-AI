Title: Title-casing helper crashes on empty product names

Description:
When the catalog import job title-cases a product name and encounters an empty name field (a known data-entry error), it throws a runtime exception instead of skipping the field.

Expected behavior:
The job should skip title-casing for an empty name instead of crashing.

Actual behavior:
The job throws an exception and the import batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the catalog import job with a product record where `name=""`.
