Title: Feature flag lookup crashes for an unregistered flag

Description:
When client code checks a feature flag that was referenced before it was registered server-side (e.g. `"beta_search"`), the flag service throws a runtime exception instead of defaulting to off.

Expected behavior:
The endpoint should default to `false` for an unregistered flag, not crash.

Actual behavior:
The endpoint throws an exception and returns HTTP 500.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/flags/check` with `flag_name="beta_search"` against a flag map containing only `{"dark_mode": true}`.
