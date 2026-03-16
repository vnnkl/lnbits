"""Tests for the orangepiller payment rerouting engine (S02)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orangepiller.models import Arrangement


def _make_arrangement(**overrides) -> Arrangement:
    defaults = dict(
        id="arr_test1",
        orange_piller_wallet="wallet_op",
        merchant_wallet="wallet_merchant",
        merchant_user_id="user_merchant",
        total_debt_sats=10000,
        repaid_sats=0,
        reroute_percent=10,
        status="active",
    )
    defaults.update(overrides)
    return Arrangement(**defaults)


def _make_payment(sat: int = 1000, tag: str | None = None, wallet_id: str = "wallet_merchant"):
    """Create a mock Payment with .sat, .wallet_id, .extra, .payment_hash."""
    payment = MagicMock()
    payment.sat = sat
    payment.amount = sat * 1000  # msat
    payment.wallet_id = wallet_id
    payment.payment_hash = "hash_abc123"
    payment.extra = {"tag": tag} if tag else {}
    return payment


class TestOnInvoicePaid:
    """Tests for the on_invoice_paid handler in tasks.py."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_successful_reroute(
        self, mock_get, mock_update, mock_create, mock_pay
    ):
        """Normal reroute: 10% of 1000 sats = 100 sats transferred."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement()
        updated_arr = _make_arrangement(repaid_sats=100)
        mock_get.return_value = arr
        mock_update.return_value = updated_arr
        mock_create.return_value = MagicMock(bolt11="lnbc100...")

        payment = _make_payment(sat=1000)
        await on_invoice_paid(payment)

        mock_update.assert_called_once_with("arr_test1", 100)
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["wallet_id"] == "wallet_op"
        assert kwargs["amount"] == 100
        assert kwargs["internal"] is True
        mock_pay.assert_called_once()

    @pytest.mark.anyio
    async def test_tag_guard_skips_orangepiller_payments(self):
        """Payments tagged 'orangepiller' are skipped to prevent infinite loops."""
        from orangepiller.tasks import on_invoice_paid

        payment = _make_payment(tag="orangepiller")
        # Should return without error and not call any CRUD
        await on_invoice_paid(payment)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_no_arrangement_skips(self, mock_get):
        """No arrangement for wallet → skip."""
        from orangepiller.tasks import on_invoice_paid

        mock_get.return_value = None
        payment = _make_payment()
        await on_invoice_paid(payment)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_completed_arrangement_skips(self, mock_get):
        """Completed arrangement → skip."""
        from orangepiller.tasks import on_invoice_paid

        mock_get.return_value = _make_arrangement(status="completed")
        payment = _make_payment()
        await on_invoice_paid(payment)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_zero_amount_skips(self, mock_get):
        """1% of 50 sats = 0 → skip."""
        from orangepiller.tasks import on_invoice_paid

        mock_get.return_value = _make_arrangement(reroute_percent=1)
        payment = _make_payment(sat=50)
        await on_invoice_paid(payment)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_cap_at_remaining_debt(self, mock_get, mock_update):
        """Reroute capped at remaining debt when percentage exceeds it."""
        from orangepiller.tasks import on_invoice_paid

        # 100% of 1000 sats = 1000, but only 50 remaining
        arr = _make_arrangement(
            reroute_percent=100, total_debt_sats=1000, repaid_sats=950
        )
        mock_get.return_value = arr
        mock_update.return_value = _make_arrangement(
            repaid_sats=1000, status="completed"
        )

        with patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock) as mock_create, \
             patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock):
            mock_create.return_value = MagicMock(bolt11="lnbc50...")
            payment = _make_payment(sat=1000)
            await on_invoice_paid(payment)

            # Should cap at 50 (remaining_debt), not 1000
            mock_update.assert_called_once_with("arr_test1", 50)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.rollback_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_rollback_on_payment_failure(
        self, mock_get, mock_update, mock_create, mock_pay, mock_rollback
    ):
        """pay_invoice failure → rollback debt update."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement()
        mock_get.return_value = arr
        mock_update.return_value = _make_arrangement(repaid_sats=100)
        mock_create.return_value = MagicMock(bolt11="lnbc100...")
        mock_pay.side_effect = Exception("payment failed")

        payment = _make_payment(sat=1000)
        await on_invoice_paid(payment)

        mock_rollback.assert_called_once_with("arr_test1", 100)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_exact_payoff(self, mock_get, mock_update, mock_create, mock_pay):
        """Remaining debt == reroute amount → transfers exact remainder, completes."""
        from orangepiller.tasks import on_invoice_paid

        # 10% of 1000 = 100, remaining = 100 → exact match
        arr = _make_arrangement(
            reroute_percent=10, total_debt_sats=1000, repaid_sats=900
        )
        mock_get.return_value = arr
        mock_update.return_value = _make_arrangement(
            repaid_sats=1000, total_debt_sats=1000, status="completed"
        )
        mock_create.return_value = MagicMock(bolt11="lnbc100...")

        payment = _make_payment(sat=1000)
        await on_invoice_paid(payment)

        # Should transfer exactly 100 (the remaining debt)
        mock_update.assert_called_once_with("arr_test1", 100)
        _, kwargs = mock_create.call_args
        assert kwargs["amount"] == 100
        mock_pay.assert_called_once()

    @pytest.mark.anyio
    @patch("orangepiller.tasks.rollback_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_rollback_on_create_invoice_failure(
        self, mock_get, mock_update, mock_create, mock_rollback
    ):
        """create_invoice failure → rollback debt update, no propagation."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement()
        mock_get.return_value = arr
        mock_update.return_value = _make_arrangement(repaid_sats=100)
        mock_create.side_effect = Exception("invoice creation failed")

        payment = _make_payment(sat=1000)
        # Should not raise
        await on_invoice_paid(payment)

        mock_rollback.assert_called_once_with("arr_test1", 100)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_atomic_update_returns_none_skips_transfer(self, mock_get, mock_update):
        """If atomic update returns None (race condition), no transfer attempted."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement()
        mock_get.return_value = arr
        mock_update.return_value = None  # Concurrent completion

        payment = _make_payment(sat=1000)
        await on_invoice_paid(payment)

        # create_invoice should never be called
        mock_update.assert_called_once()

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_uses_payment_sat_not_msat(
        self, mock_get, mock_update, mock_create, mock_pay
    ):
        """Verifies payment.sat (sats) is used, not payment.amount (msat)."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_arrangement(reroute_percent=10)
        mock_get.return_value = arr
        mock_update.return_value = _make_arrangement(repaid_sats=5)
        mock_create.return_value = MagicMock(bolt11="lnbc5...")

        # payment.sat = 50, payment.amount = 50000 (msat)
        payment = _make_payment(sat=50)
        await on_invoice_paid(payment)

        # 10% of 50 sats = 5, not 10% of 50000
        mock_update.assert_called_once_with("arr_test1", 5)
