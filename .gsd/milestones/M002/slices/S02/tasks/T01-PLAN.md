---
estimated_steps: 7
estimated_files: 2
---

# T01: Add TPoS, QR, credentials, and poster columns to both dashboards

**Slice:** S02 — Dashboards, QR codes & printable poster
**Milestone:** M002

## Description

Wire TPoS links, QR code dialogs, merchant credentials, and poster links into both dashboard tables. The orange piller table gets four new affordances: merchant name column, TPoS link + QR button + poster link (combined "tpos" column), and a credentials copy button. The merchant table gets a TPoS link + QR button column. A shared QR dialog reuses the existing `<lnbits-qrcode>` component. All TPoS UI is guarded against null `tpos_url`.

## Steps

1. In `index.js`, add `showQrDialog: false` and `qrDialogUrl: ''` to `data()`. Add `showQr(url)` method that sets both fields. Add three new column definitions to `columns` array: `merchant_name` (text), `tpos` (custom slot), `merchant_credentials` (custom slot). Insert them after `merchant_wallet` and before `total_debt_sats`. Add `tpos` column to `merchantColumns` after `orange_piller_wallet`.

2. In `index.html`, add `<template v-slot:body-cell-tpos="props">` in the orange piller table: if `props.row.tpos_url`, show a `<q-btn>` icon link (open_in_new) opening the TPoS URL, a `<q-btn>` icon (qr_code_2) calling `showQr(props.row.tpos_url)`, and a `<q-btn>` icon (print) linking to `/orangepiller/poster/${props.row.id}`. If no `tpos_url`, show `<q-chip>` "No TPoS" in grey.

3. In `index.html`, add `<template v-slot:body-cell-merchant_credentials="props">` in the orange piller table: a truncated link + `<q-btn>` copy icon calling `copyText(props.row.merchant_credentials)`.

4. In `index.html`, add `<template v-slot:body-cell-tpos="props">` in the merchant table: same TPoS link + QR button pattern, minus poster and credentials (merchants don't need those). Guard with `v-if="props.row.tpos_url"`.

5. In `index.html`, add the QR dialog after the existing forgive dialog: `<q-dialog v-model="showQrDialog">` containing `<q-card>` with `<lnbits-qrcode :value="qrDialogUrl">`.

6. In the orange piller completion toast (`_detectCompletionTransitions`), update the label to use `merchant_name` when available: `a.merchant_name || a.merchant_wallet`.

7. Verify: grep for all new terms in both files; visual structure check of column order and slot names.

## Must-Haves

- [ ] Orange piller table has `merchant_name`, `tpos`, `merchant_credentials` columns
- [ ] Merchant table has `tpos` column
- [ ] QR dialog uses `<lnbits-qrcode>` component, opens via `showQr()` method
- [ ] All TPoS UI guarded with `v-if` on `tpos_url` — shows "No TPoS" chip when null
- [ ] Credentials copy uses `copyText()` from windowMixin
- [ ] Poster link points to `/orangepiller/poster/{arrangement_id}`

## Verification

- `grep -c 'merchant_name\|tpos_url\|lnbits-qrcode\|showQrDialog\|merchant_credentials\|poster' orangepiller/static/js/index.js orangepiller/templates/orangepiller/index.html` — all terms present
- Column count in `columns` array increased from 9 to 12; `merchantColumns` from 7 to 8
- Body-cell slot names match column names in both tables

## Inputs

- `orangepiller/static/js/index.js` — existing columns arrays, data(), methods (from M001/S03-S04)
- `orangepiller/templates/orangepiller/index.html` — existing body-cell slots, dialog pattern (from M001/S03-S04)
- S01 provides: `tpos_url`, `merchant_name`, `merchant_credentials`, `tpos_id` fields on Arrangement — returned by GET endpoints via `SELECT *`

## Expected Output

- `orangepiller/static/js/index.js` — 3 new columns in `columns`, 1 new column in `merchantColumns`, QR dialog state + method, poster link helper
- `orangepiller/templates/orangepiller/index.html` — 3 new body-cell slots in orange piller table, 1 in merchant table, QR dialog markup

## Observability Impact

- **New client-side state:** `showQrDialog` (boolean) and `qrDialogUrl` (string) on the Vue app — inspectable via browser console `window.app._instance.data`.
- **Failure signals:** If `tpos_url` is null, the UI renders a grey "No TPoS" chip instead of link/QR buttons — visually verifiable, no silent failure.
- **Credentials handling:** `merchant_credentials` is rendered truncated and copied via `copyText()`. No new network requests or console logging — credential value stays client-side only.
- **Inspection:** Column arrays are runtime-inspectable; slot presence is verifiable via DOM inspection of `<td>` elements with `data-col` attributes in Quasar tables.
