# S01: Fiat Reroute Engine — UAT

## Prerequisites
- LNbits running at `localhost:5001` with orangepiller extension
- Admin logged in

## Tests

### 1. Create a fiat arrangement via API
```bash
curl -X POST http://localhost:5001/orangepiller/api/v1/arrangements \
  -H "X-Api-Key: <admin_key>" \
  -H "Content-Type: application/json" \
  -d '{"debt_currency":"EUR","total_debt_fiat":100.0,"total_debt_sats":0,"reroute_percent":50,"merchant_name":"Test Fiat Merchant"}'
```
- [ ] Response includes `debt_currency: "EUR"`, `total_debt_fiat: 100.0`, `repaid_fiat: 0`
- [ ] `total_debt_sats` is 0

### 2. Create a sat arrangement (backward compat)
```bash
curl -X POST http://localhost:5001/orangepiller/api/v1/arrangements \
  -H "X-Api-Key: <admin_key>" \
  -H "Content-Type: application/json" \
  -d '{"total_debt_sats":50000,"reroute_percent":10,"merchant_name":"Test Sat Merchant"}'
```
- [ ] Response includes `debt_currency: "sat"`, `total_debt_sats: 50000`
- [ ] `total_debt_fiat` is null

### 3. Verify migration
- [ ] Both arrangements appear in GET /orangepiller/api/v1/arrangements
- [ ] Existing arrangements from M002 testing still appear with `debt_currency: "sat"`
