## Why

When loading an army file, the validator reports equipment requirement failures with a generic message ("requires are not satisfied") that tells the user *what* failed but not *why*. A player who manually edits a JSON army file needs to know which specific equipment limit or type constraint is violated so they can fix it without trial-and-error.

## What Changes

- The `validate_army` function (and its helper `_satisfies_requires`) will produce richer error messages that identify the specific requirement group(s) that failed.
- Error messages will name the failing constraint—e.g., `needs Hands:2 but only 0 available` or `requires type Infantry, Grunt`.

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `army-load-validation`: The equipment-requires validation error message is changing to include which constraint group(s) were unsatisfied.

## Impact

- `src/spf/armies/data.py`: `_satisfies_requires` and `validate_army` change their error reporting.
- `tests/armies/test_data.py`: Existing tests that assert on the old message text will need updating; new test cases covering the detail messages.

## Non-goals

- Changing *when* validation fails (only the message changes).
- Reporting all failing slots in a single combined message (per-group reporting is sufficient).
- Changing validation behavior for the CLI `show` command exit code or error formatting.
