"""Tests for the merchant GET and arrangement PUT endpoints (S04/T01)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from orangepiller.models import Arrangement, UpdateArrangement


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


def _make_key_info(wallet_id: str):
    """Create a mock WalletTypeInfo with wallet.id set."""
    key_info = MagicMock()
    key_info.wallet = MagicMock()
    key_info.wallet.id = wallet_id
    return key_info


class TestMerchantGetEndpoint:
    """Tests for GET /api/v1/merchant/arrangements."""

    @pytest.mark.anyio
    @patch(
        "orangepiller.views_api.get_arrangement_by_merchant_wallet",
        new_callable=AsyncMock,
    )
    async def test_merchant_get_returns_own_arrangement(self, mock_get):
        """Merchant GET returns arrangements matching the authenticated merchant_wallet."""
        from orangepiller.views_api import api_get_merchant_arrangements

        arr = _make_arrangement()
        mock_get.return_value = arr
        key_info = _make_key_info("wallet_merchant")

        result = await api_get_merchant_arrangements(key_info=key_info)

        mock_get.assert_called_once_with("wallet_merchant")
        assert len(result) == 1
        assert result[0].id == "arr_test1"


class TestPutEndpoint:
    """Tests for PUT /api/v1/arrangements/{arrangement_id}."""

    @pytest.mark.anyio
    @patch("orangepiller.views_api.get_arrangement", new_callable=AsyncMock)
    async def test_put_rejects_unauthorized(self, mock_get):
        """Wallet ID mismatch → 403."""
        from fastapi import HTTPException
        from orangepiller.views_api import api_update_arrangement

        mock_get.return_value = _make_arrangement(orange_piller_wallet="wallet_op")
        key_info = _make_key_info("wallet_other")  # not the owner
        data = UpdateArrangement(reroute_percent=50)

        with pytest.raises(HTTPException) as exc_info:
            await api_update_arrangement(
                arrangement_id="arr_test1", data=data, key_info=key_info
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.anyio
    @patch("orangepiller.views_api.get_arrangement", new_callable=AsyncMock)
    async def test_put_rejects_completed_arrangement(self, mock_get):
        """Percent update on completed arrangement → 400."""
        from fastapi import HTTPException
        from orangepiller.views_api import api_update_arrangement

        mock_get.return_value = _make_arrangement(status="completed")
        key_info = _make_key_info("wallet_op")
        data = UpdateArrangement(reroute_percent=50)

        with pytest.raises(HTTPException) as exc_info:
            await api_update_arrangement(
                arrangement_id="arr_test1", data=data, key_info=key_info
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.anyio
    @patch("orangepiller.views_api.update_arrangement", new_callable=AsyncMock)
    @patch("orangepiller.views_api.get_arrangement", new_callable=AsyncMock)
    async def test_put_forgiveness(self, mock_get, mock_update):
        """Forgiveness sets repaid_sats = total_debt_sats and status = completed."""
        from orangepiller.views_api import api_update_arrangement

        arr = _make_arrangement(total_debt_sats=10000)
        mock_get.return_value = arr
        forgiven = _make_arrangement(
            repaid_sats=10000, status="completed"
        )
        mock_update.return_value = forgiven
        key_info = _make_key_info("wallet_op")
        data = UpdateArrangement(forgive=True)

        result = await api_update_arrangement(
            arrangement_id="arr_test1", data=data, key_info=key_info
        )

        mock_update.assert_called_once_with(
            "arr_test1", repaid_sats=10000, status="completed"
        )
        assert result.status == "completed"
        assert result.repaid_sats == 10000

    @pytest.mark.anyio
    @patch("orangepiller.views_api.update_arrangement", new_callable=AsyncMock)
    @patch("orangepiller.views_api.get_arrangement", new_callable=AsyncMock)
    async def test_put_percent_update(self, mock_get, mock_update):
        """Valid percent updates arrangement."""
        from orangepiller.views_api import api_update_arrangement

        arr = _make_arrangement(reroute_percent=10)
        mock_get.return_value = arr
        updated = _make_arrangement(reroute_percent=50)
        mock_update.return_value = updated
        key_info = _make_key_info("wallet_op")
        data = UpdateArrangement(reroute_percent=50)

        result = await api_update_arrangement(
            arrangement_id="arr_test1", data=data, key_info=key_info
        )

        mock_update.assert_called_once_with("arr_test1", reroute_percent=50)
        assert result.reroute_percent == 50

    @pytest.mark.anyio
    @patch("orangepiller.views_api.get_arrangement", new_callable=AsyncMock)
    async def test_put_percent_validation(self, mock_get):
        """Percent outside 1–100 → 400."""
        from fastapi import HTTPException
        from orangepiller.views_api import api_update_arrangement

        mock_get.return_value = _make_arrangement()
        key_info = _make_key_info("wallet_op")

        for bad_value in [0, 101, -5]:
            data = UpdateArrangement(reroute_percent=bad_value)
            with pytest.raises(HTTPException) as exc_info:
                await api_update_arrangement(
                    arrangement_id="arr_test1", data=data, key_info=key_info
                )
            assert exc_info.value.status_code == 400
