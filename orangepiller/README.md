# Orange Piller - <small>[LNbits](https://github.com/lnbits/lnbits) extension</small>

## Onboard merchants to Bitcoin with managed LNbits accounts and payback arrangements

Orange Piller helps Bitcoin evangelists ("orange pillers") onboard merchants by setting up managed LNbits wallets with automated payback arrangements. The orange piller funds a merchant's initial setup, and the extension automatically routes a percentage of the merchant's incoming payments back to the orange piller until the debt is repaid.

## Features

- **Merchant Onboarding:** Create managed LNbits wallets for new merchants with a single action
- **Payback Arrangements:** Define payback terms including total amount and percentage split on incoming payments
- **Automatic Rerouting:** Incoming payments to the merchant wallet are automatically split, routing the configured percentage back to the orange piller
- **Cutover Detection:** When the debt is fully repaid, rerouting stops automatically and the arrangement is marked as completed
- **Dual Dashboards:** Both the orange piller and the merchant can track arrangement status and progress

## Installation

Install via the LNbits extension manager:

1. Open your LNbits instance
2. Go to **Manage Extensions**
3. Click **Add extension** and enter the GitHub repository URL
4. Enable the Orange Piller extension

Or install manually by cloning into your LNbits `extensions/` directory:

```bash
cd lnbits/extensions
git clone https://github.com/lnbits/orangepiller.git
```

## Usage

### As an Orange Piller

1. Enable the extension and select your funding wallet
2. Click **New Arrangement** to onboard a merchant
3. Set the payback amount and percentage split
4. The extension creates a managed wallet for the merchant and begins tracking repayment

### As a Merchant

1. Access your merchant dashboard via the provided link
2. View your arrangement status, repayment progress, and wallet balance
3. Accept payments normally — the payback split is handled automatically
4. Once the debt is repaid, your wallet operates independently

## Requirements

- LNbits >= 1.3.0

## License

MIT — see [LICENSE](LICENSE) for details.
