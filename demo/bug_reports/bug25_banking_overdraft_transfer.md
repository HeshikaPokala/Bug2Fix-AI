Title: Funds transfer crashes when amount exceeds source balance

Description:
When a customer requests a transfer larger than their source account balance, the transfer service throws a runtime exception instead of a clean decline.

Expected behavior:
The endpoint should return a 402 decline response, not crash.

Actual behavior:
The endpoint throws an exception and the transfer request fails ungracefully.

Environment:
- Python 3.11
- macOS
- Service version: 2.2.0

Reproduction hints:
- Trigger `/banking/transfer` for an account with `source_balance=200` requesting `transfer_amount=500`.
