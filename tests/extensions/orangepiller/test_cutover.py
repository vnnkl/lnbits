"""Tests for the orangepiller cutover path: debt completion, status
transition, and subsequent payment skipping (S05 / R010)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orangepiller.models import Arrangement


def _make_arrangement(**overrides) -> Arrangement:
    defaults = dict(
        id="arr_cutover",
        orange_piller_wallet="wallet_op",
        merchant_wallet="wallet_merchant",
        merchant_user_id="user_merchant",
        total_debt_sats=10000,
        repaid_sats=0,
        reroute_percent=50,
        status="active",
    )
    defaults.update(overrides)
    return Arrangement(**defaults)


def _make_payment(sat: int = 1000, wallet_id: str = "wallet_merchant"):
    payment = MagicMock()
    payment.sat = sat
    payment.amount = sat * 1000
    payment.wallet_id = wallet_id
    payment.payment_hash = "hash_cutover"
    payment.extra = {}
    return payment


class TestDebtCutover:
    """Cutover path: debt reaches zero → status completed → skip."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_debt_completion_transitions_status(
        self, mock_get, mock_update, mock_create, mock_pay
    ):
        """When repaid sats meet total debt, status transitions to 'completed'
        and repaid_sats equals total_debt_sats (capped, not exceeded)."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement(
            total_debt_sats=5000, repaid_sats=4000, reroute_percent=50
        )
        # Payment of 2000 at 50% = 1000 reroute, but only 1000 remaining
        completed_arr = _make_arrangement(
            total_debt_sats=5000, repaid_sats=5000, status="completed"
        )
        mock_get.return_value = arr
        mock_update.return_value = completed_arr
        mock_create.return_value = MagicMock(bolt11="lnbc1000...")

        payment = _make_payment(sat=2000)
        await on_invoice_paid(payment)

        # Reroute capped at remaining debt (1000), not 50% of 2000 (1000) — equal here
        mock_update.assert_called_once_with("arr_cutover", 1000)
        # Verify the returned arrangement reflects completion
        assert completed_arr.status == "completed"
        assert completed_arr.repaid_sats == completed_arr.total_debt_sats

    @pytest.mark.anyio
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_completed_arrangement_skipped(
        self, mock_get, mock_update, mock_create
    ):
        """An arrangement with status='completed' is skipped entirely —
        no debt update and no transfer attempted."""
        from orangepiller.tasks import on_invoice_paid

        mock_get.return_value = _make_arrangement(
            status="completed", total_debt_sats=5000, repaid_sats=5000
        )

        payment = _make_payment(sat=3000)
        await on_invoice_paid(payment)

        mock_update.assert_not_called()
        mock_create.assert_not_called()

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_exact_payoff_caps_and_completes(
        self, mock_get, mock_update, mock_create, mock_pay
    ):
        """Payment of 5000 at 50% = 2500 reroute, but only 1000 remaining.
        Only 1000 sats should be rerouted and arrangement completes."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement(
            total_debt_sats=10000, repaid_sats=9000, reroute_percent=50
        )
        completed_arr = _make_arrangement(
            total_debt_sats=10000, repaid_sats=10000, status="completed"
        )
        mock_get.return_value = arr
        mock_update.return_value = completed_arr
        mock_create.return_value = MagicMock(bolt11="lnbc1000...")

        payment = _make_payment(sat=5000)
        await on_invoice_paid(payment)

        # 50% of 5000 = 2500, but remaining = 1000 → capped at 1000
        mock_update.assert_called_once_with("arr_cutover", 1000)
        _, create_kwargs = mock_create.call_args
        assert create_kwargs["amount"] == 1000
        mock_pay.assert_called_once()
        assert completed_arr.status == "completed"
        assert completed_arr.repaid_sats == completed_arr.total_debt_sats
