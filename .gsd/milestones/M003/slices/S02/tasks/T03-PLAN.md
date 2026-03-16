---
estimated_steps: 4
estimated_files: 0
---

# T03: Live Docker verification and polish

**Slice:** S02 — Dashboard fiat display and onboarding form
**Milestone:** M003

## Description

End-to-end verification on the running Docker instance. Create fiat and sat arrangements through the UI, verify display, check edge cases, and fix any visual issues.

## Steps

1. Navigate to `localhost:5001/orangepiller/` and create a new EUR arrangement (€100, 50% reroute, "Test EUR Merchant") via the onboard form
2. Verify the arrangement table shows EUR amounts: "€100.00" for Total Debt, "€0.00" for Repaid, "€100.00" for Remaining, 0% progress
3. Create a sat arrangement via the same form, verify it shows sats as before
4. Check that existing arrangements (from M002 testing) still display correctly. Verify the merchant dashboard displays fiat correctly. Verify the poster page still works. Fix any visual issues found

## Must-Haves

- [ ] EUR arrangement created via UI and displays with € symbol
- [ ] Sat arrangement created via UI and displays in sats
- [ ] Both types coexist in the same table
- [ ] Poster page still works for both types
- [ ] All tests pass

## Verification

- Screenshots of dashboard showing fiat and sat arrangements
- `pytest tests/extensions/orangepiller/ -v` — all tests pass
- Browser assertions for key UI elements

## Inputs

- Docker instance at `localhost:5001` with orangepiller extension
- S02/T01 and S02/T02 completed code

## Expected Output

- Visual confirmation that the full flow works
- Minor CSS/formatting fixes if needed
