Title: Calendar sync crashes on out-of-range month index

Description:
When the third-party calendar API sends a month index outside the valid 0-11 range (a known off-by-one bug in their integration), the calendar sync service throws a runtime exception instead of skipping the malformed entry.

Expected behavior:
The service should skip / reject an out-of-range month index with a clear validation error, not crash.

Actual behavior:
The service throws an exception and the whole sync batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the calendar sync job with a month index of 14 (outside the valid 0-11 range).
