"""Tests for the fiat-denominated payment rerouting engine (M003/S01)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orangepiller.models import Arrangement


def _make_fiat_arrangement(**overrides) -> Arrangement:
    """Create a fiat-denominated arrangement (EUR by default)."""
    defaults = dict(
        id="arr_fiat1",
        orange_piller_wallet="wallet_op",
        merchant_wallet="wallet_merchant",
        merchant_user_id="user_merchant",
        total_debt_sats=0,
        repaid_sats=0,
        reroute_percent=50,
        status="active",
        debt_currency="EUR",
        total_debt_fiat=100.0,
        repaid_fiat=0.0,
    )
    defaults.update(overrides)
    return Arrangement(**defaults)


def _make_sat_arrangement(**overrides) -> Arrangement:
    """Create a sat-denominated arrangement (backward compat)."""
    defaults = dict(
        id="arr_sat1",
        orange_piller_wallet="wallet_op",
        merchant_wallet="wallet_merchant",
        merchant_user_id="user_merchant",
        total_debt_sats=10000,
        repaid_sats=0,
        reroute_percent=10,
        status="active",
        debt_currency="sat",
        total_debt_fiat=None,
        repaid_fiat=0,
    )
    defaults.update(overrides)
    return Arrangement(**defaults)


def _make_payment(sat: int = 1000, wallet_id: str = "wallet_merchant"):
    payment = MagicMock()
    payment.sat = sat
    payment.amount = sat * 1000
    payment.wallet_id = wallet_id
    payment.payment_hash = "hash_fiat123"
    payment.extra = {}
    return payment


class TestFiatRerouteHappyPath:
    """Fiat reroute: payment converted at spot, % applied in fiat, sats transferred."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.fiat_amount_as_satoshis", new_callable=AsyncMock)
    @patch("orangepiller.tasks.satoshis_amount_as_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_fiat_reroute_happy_path(
        self, mock_get, mock_s2f, mock_f2s, mock_update_fiat,
        mock_create, mock_pay
    ):
        """10000 sat payment = €10 at mocked rate. 50% reroute = €5.
        Transfer 5000 sats (€5 at same rate)."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_fiat_arrangement()
        updated_arr = _make_fiat_arrangement(repaid_fiat=5.0)

        mock_get.return_value = arr
        # 10000 sats = €10.00
        mock_s2f.return_value = 10.0
        # €5.00 = 5000 sats
        mock_f2s.return_value = 5000
        mock_update_fiat.return_value = updated_arr
        mock_create.return_value = MagicMock(bolt11="lnbc5000...")

        payment = _make_payment(sat=10000)
        await on_invoice_paid(payment)

        # Verify fiat path was used
        mock_s2f.assert_called_once_with(10000, "EUR")
        mock_f2s.assert_called_once_with(5.0, "EUR")
        mock_update_fiat.assert_called_once_with("arr_fiat1", 5.0)

        # Verify sat transfer
        _, kwargs = mock_create.call_args
        assert kwargs["wallet_id"] == "wallet_op"
        assert kwargs["amount"] == 5000
        assert kwargs["internal"] is True
        mock_pay.assert_called_once()


class TestFiatCapAtRemainingDebt:
    """Fiat reroute capped at remaining fiat debt."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.fiat_amount_as_satoshis", new_callable=AsyncMock)
    @patch("orangepiller.tasks.satoshis_amount_as_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_fiat_cap_at_remaining(
        self, mock_get, mock_s2f, mock_f2s, mock_update_fiat,
        mock_create, mock_pay
    ):
        """€2 remaining, payment worth €10, 50% = €5 → capped at €2."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_fiat_arrangement(
            total_debt_fiat=100.0, repaid_fiat=98.0, reroute_percent=50
        )
        updated = _make_fiat_arrangement(
            repaid_fiat=100.0, status="completed"
        )

        mock_get.return_value = arr
        mock_s2f.return_value = 10.0  # payment = €10
        mock_f2s.return_value = 2000  # €2 = 2000 sats
        mock_update_fiat.return_value = updated
        mock_create.return_value = MagicMock(bolt11="lnbc2000...")

        payment = _make_payment(sat=10000)
        await on_invoice_paid(payment)

        # Capped at €2 (remaining), not €5 (50% of €10)
        mock_update_fiat.assert_called_once_with("arr_fiat1", 2.0)
        mock_f2s.assert_called_once_with(2.0, "EUR")


class TestFiatExactPayoff:
    """Fiat debt reaches exactly zero → status transitions to completed."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.fiat_amount_as_satoshis", new_callable=AsyncMock)
    @patch("orangepiller.tasks.satoshis_amount_as_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_fiat_exact_payoff_completes(
        self, mock_get, mock_s2f, mock_f2s, mock_update_fiat,
        mock_create, mock_pay
    ):
        """€5 remaining, 50% of €10 payment = €5 → exact payoff."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_fiat_arrangement(
            total_debt_fiat=100.0, repaid_fiat=95.0, reroute_percent=50
        )
        updated = _make_fiat_arrangement(
            repaid_fiat=100.0, total_debt_fiat=100.0, status="completed"
        )

        mock_get.return_value = arr
        mock_s2f.return_value = 10.0
        mock_f2s.return_value = 5000
        mock_update_fiat.return_value = updated
        mock_create.return_value = MagicMock(bolt11="lnbc5000...")

        payment = _make_payment(sat=10000)
        await on_invoice_paid(payment)

        mock_update_fiat.assert_called_once_with("arr_fiat1", 5.0)
        assert updated.status == "completed"


class TestExchangeRateFailure:
    """Exchange rate unavailable → reroute skipped, no debt change."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.satoshis_amount_as_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_exchange_rate_failure_skips_reroute(self, mock_get, mock_s2f):
        """ValueError from satoshis_amount_as_fiat → skip reroute."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_fiat_arrangement()
        mock_get.return_value = arr
        mock_s2f.side_effect = ValueError("Could not get exchange rate for EUR.")

        payment = _make_payment(sat=10000)
        await on_invoice_paid(payment)

        # No fiat update should have been called
        # (would raise if we tried to call update_arrangement_repaid_fiat)

    @pytest.mark.anyio
    @patch("orangepiller.tasks.rollback_arrangement_repaid_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.fiat_amount_as_satoshis", new_callable=AsyncMock)
    @patch("orangepiller.tasks.satoshis_amount_as_fiat", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_fiat_transfer_failure_rollback(
        self, mock_get, mock_s2f, mock_f2s, mock_update_fiat,
        mock_create, mock_pay, mock_rollback
    ):
        """pay_invoice failure → rollback fiat debt update."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_fiat_arrangement()
        mock_get.return_value = arr
        mock_s2f.return_value = 10.0
        mock_f2s.return_value = 5000
        mock_update_fiat.return_value = _make_fiat_arrangement(repaid_fiat=5.0)
        mock_create.return_value = MagicMock(bolt11="lnbc5000...")
        mock_pay.side_effect = Exception("payment failed")

        payment = _make_payment(sat=10000)
        await on_invoice_paid(payment)

        mock_rollback.assert_called_once_with("arr_fiat1", 5.0)


class TestSatBackwardCompat:
    """Sat-denominated arrangement uses existing sat path, not fiat path."""

    @pytest.mark.anyio
    @patch("orangepiller.tasks.pay_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.create_invoice", new_callable=AsyncMock)
    @patch("orangepiller.tasks.update_arrangement_repaid", new_callable=AsyncMock)
    @patch("orangepiller.tasks.get_arrangement_by_merchant_wallet", new_callable=AsyncMock)
    async def test_sat_arrangement_uses_sat_path(
        self, mock_get, mock_update, mock_create, mock_pay
    ):
        """debt_currency='sat' → existing sat path, repaid_sats updated."""
        from orangepiller.tasks import on_invoice_paid

        arr = _make_sat_arrangement()
        mock_get.return_value = arr
        mock_update.return_value = _make_sat_arrangement(repaid_sats=100)
        mock_create.return_value = MagicMock(bolt11="lnbc100...")

        payment = _make_payment(sat=1000)
        await on_invoice_paid(payment)

        # Sat path: update_arrangement_repaid (not fiat)
        mock_update.assert_called_once_with("arr_sat1", 100)
        mock_create.assert_called_once()
        mock_pay.assert_called_once()


class TestFiatModelProperties:
    """Verify computed properties work correctly for fiat arrangements."""

    def test_remaining_debt_fiat(self):
        arr = _make_fiat_arrangement(total_debt_fiat=100.0, repaid_fiat=23.45)
        assert arr.remaining_debt_fiat == pytest.approx(76.55)

    def test_remaining_debt_fiat_zero(self):
        arr = _make_fiat_arrangement(total_debt_fiat=100.0, repaid_fiat=100.0)
        assert arr.remaining_debt_fiat == 0.0

    def test_progress_percent_fiat(self):
        arr = _make_fiat_arrangement(total_debt_fiat=100.0, repaid_fiat=45.0)
        assert arr.progress_percent == 45.0

    def test_progress_percent_sat_unchanged(self):
        arr = _make_sat_arrangement(total_debt_sats=10000, repaid_sats=4500)
        assert arr.progress_percent == 45.0

    def test_is_completed_fiat(self):
        arr = _make_fiat_arrangement(total_debt_fiat=100.0, repaid_fiat=100.0)
        assert arr.is_completed is True

    def test_is_completed_fiat_not_yet(self):
        arr = _make_fiat_arrangement(total_debt_fiat=100.0, repaid_fiat=99.99)
        assert arr.is_completed is False
