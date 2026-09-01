Title: Restock alert crashes when warehouse reports no stock data

Description:
When the inventory feed sends an empty stock-levels list for a warehouse, the nightly restock-alert job throws a runtime exception instead of skipping the check.

Expected behavior:
The job should skip the alert check gracefully when no stock data is present.

Actual behavior:
The job throws an exception and the nightly batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.0.1

Reproduction hints:
- Run the nightly restock job for a warehouse with an empty `stock_levels` payload (no SKUs reported).
