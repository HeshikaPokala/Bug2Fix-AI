Title: Account email lookup crashes for records missing an email field

Description:
When the account service looks up a display email for a legacy record with no email field, it throws a runtime exception and returns HTTP 500 instead of a placeholder.

Expected behavior:
The endpoint should return a placeholder (e.g. "no email on file") when the field is missing.

Actual behavior:
The endpoint throws an exception and fails the request.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/accounts/lookup-email` for a legacy account record with no `email` field.
