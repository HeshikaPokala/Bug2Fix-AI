Title: Translation lookup crashes for an unsupported locale

Description:
When a request specifies a locale that hasn't been translated yet (e.g. `"de"`), the i18n service throws a runtime exception instead of falling back to English.

Expected behavior:
The endpoint should fall back to English for an unsupported locale, not crash.

Actual behavior:
The endpoint throws an exception and returns HTTP 500.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/i18n/translate` with `locale="de"` against a translation map containing only `{"en": ..., "fr": ...}`.
