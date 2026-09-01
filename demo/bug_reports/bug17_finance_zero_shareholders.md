Title: Dividend calculator crashes for entities with zero shareholders

Description:
When the dividend batch job processes an entity mid-migration with zero shareholders on record, it throws a runtime exception instead of skipping the entity.

Expected behavior:
The job should skip an entity with zero shareholders, not crash the whole batch.

Actual behavior:
The job throws an exception and the dividend batch fails.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger the dividend batch job for an entity with `shareholders=0`.
