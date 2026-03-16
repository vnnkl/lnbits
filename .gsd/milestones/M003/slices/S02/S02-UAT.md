# S02: Dashboard Fiat Display — UAT

## Prerequisites
- LNbits running at `localhost:5001`
- Admin logged in

## Tests

### 1. Onboarding form currency switching
- [ ] Open Onboard Merchant dialog
- [ ] Currency dropdown defaults to "sat", debt label says "Total Debt (sats) *"
- [ ] Select "EUR" → label changes to "Total Debt (EUR) *"
- [ ] Select "USD" → label changes to "Total Debt (USD) *"
- [ ] Type a custom currency and confirm it's accepted

### 2. Create a fiat arrangement
- [ ] Select EUR, enter 100, 50% reroute, name "My EUR Merchant"
- [ ] Click Onboard → success toast
- [ ] Table shows "100.00 EUR" in Total Debt, "0.00 EUR" in Repaid, "100.00 EUR" in Remaining

### 3. Create a sat arrangement
- [ ] Select sat, enter 10000, 20% reroute, name "My Sat Merchant"
- [ ] Table shows "10,000 sats" in Total Debt, "0 sats" in Repaid

### 4. Both types coexist
- [ ] Both EUR and sat rows visible in same table
- [ ] Progress bars at 0% for both
- [ ] Edit and Forgive buttons work for both types
