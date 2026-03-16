"""Tests for TPoS integration and graceful degradation (S01/T03).

Proves three risk retirements:
1. Cross-extension HTTP calls to TPoS (happy path)
2. TPoS installation detection with graceful degradation
3. Merchant credential surfacing regardless of TPoS status
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from orangepiller.models import Arrangement, CreateArrangement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_user(user_id="user_m1", wallet_id="wallet_m1", adminkey="ak_test"):
    """Return a MagicMock User with id, wallets[0].id, wallets[0].adminkey."""
    wallet = MagicMock()
    wallet.id = wallet_id
    wallet.adminkey = adminkey
    user = MagicMock()
    user.id = user_id
    user.wallets = [wallet]
    return user


def _make_mock_httpx_response(tpos_id="tpos_123"):
    """Return a mock httpx response with .json() → {"id": tpos_id}."""
    resp = MagicMock()
    resp.json.return_value = {"id": tpos_id}
    resp.raise_for_status = MagicMock()  # does nothing
    return resp


def _make_arrangement(**overrides) -> Arrangement:
    """Return an Arrangement with sensible defaults, accepting overrides."""
    defaults = dict(
        id="arr_new",
        orange_piller_wallet="wallet_op",
        merchant_wallet="wallet_m1",
        merchant_user_id="user_m1",
        total_debt_sats=50000,
        repaid_sats=0,
        reroute_percent=15,
        status="active",
    )
    defaults.update(overrides)
    return Arrangement(**defaults)


def _make_create_data(**overrides) -> CreateArrangement:
    """Return a CreateArrangement with sensible defaults."""
    defaults = dict(
        total_debt_sats=50000,
        reroute_percent=15,
        merchant_name="Alice's Coffee",
        currency="USD",
        tip_options="[10,15,20]",
        tax_default=0.07,
        tax_inclusive=True,
        business_name="Alice LLC",
        business_address="123 Main St",
        business_vat_id="VAT123",
    )
    defaults.update(overrides)
    return CreateArrangement(**defaults)


def _make_key_info(wallet_id="wallet_op"):
    """Create a mock WalletTypeInfo with wallet.id set."""
    key_info = MagicMock()
    key_info.wallet = MagicMock()
    key_info.wallet.id = wallet_id
    return key_info


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

_PATCH_PREFIX = "orangepiller.views_api"


class TestCreateArrangementWithTpos:
    """TPoS installed, httpx succeeds → tpos_id, tpos_url, merchant_credentials populated."""

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_create_arrangement_with_tpos(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        from orangepiller.views_api import api_create_arrangement

        # --- Setup ---
        mock_get_ext.return_value = MagicMock()  # non-None → installed
        mock_create_user.return_value = _make_mock_user()
        mock_settings.lnbits_baseurl = "http://localhost:5000/"

        # The arrangement returned by create_arrangement (before warning is set)
        returned_arr = _make_arrangement(
            tpos_id="tpos_123",
            tpos_url="http://localhost:5000/tpos/tpos_123",
            merchant_credentials="http://localhost:5000/wallet?usr=user_m1",
        )
        mock_create_arr.return_value = returned_arr

        # Mock httpx.AsyncClient as async context manager
        mock_response = _make_mock_httpx_response("tpos_123")
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cm = MagicMock()
        mock_client_cm.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cm.__aexit__ = AsyncMock(return_value=False)

        data = _make_create_data()
        key_info = _make_key_info()

        with patch("orangepiller.views_api.httpx.AsyncClient", return_value=mock_client_cm):
            result = await api_create_arrangement(data=data, key_info=key_info)

        # --- Assertions ---
        # httpx POST was called with correct URL and admin key header
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "http://localhost:5000/tpos/api/v1/tposs"
        assert call_args[1]["headers"] == {"X-Api-Key": "ak_test"}

        # create_arrangement was called with tpos fields populated
        mock_create_arr.assert_called_once()
        call_kwargs = mock_create_arr.call_args[1]
        assert call_kwargs["tpos_id"] == "tpos_123"
        assert call_kwargs["tpos_url"] == "http://localhost:5000/tpos/tpos_123"
        assert call_kwargs["merchant_credentials"] == "http://localhost:5000/wallet?usr=user_m1"

        # Returned arrangement has no warning on happy path
        assert result.warning is None

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_httpx_called_with_tpos_payload(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        """Verify the TPoS payload includes merchant_name, currency, and tax fields."""
        from orangepiller.views_api import api_create_arrangement

        mock_get_ext.return_value = MagicMock()
        mock_create_user.return_value = _make_mock_user()
        mock_settings.lnbits_baseurl = "http://localhost:5000/"
        mock_create_arr.return_value = _make_arrangement()

        mock_response = _make_mock_httpx_response()
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cm = MagicMock()
        mock_client_cm.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cm.__aexit__ = AsyncMock(return_value=False)

        data = _make_create_data()
        key_info = _make_key_info()

        with patch("orangepiller.views_api.httpx.AsyncClient", return_value=mock_client_cm):
            await api_create_arrangement(data=data, key_info=key_info)

        payload = mock_client_instance.post.call_args[1]["json"]
        assert payload["name"] == "Alice's Coffee"
        assert payload["currency"] == "USD"
        assert payload["tax_default"] == 0.07
        assert payload["tax_inclusive"] is True
        assert payload["wallet"] == "wallet_m1"


class TestCreateArrangementWithoutTpos:
    """TPoS not installed → tpos_id=None, warning present, merchant_credentials still populated."""

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_create_arrangement_without_tpos(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        from orangepiller.views_api import api_create_arrangement

        mock_get_ext.return_value = None  # TPoS not installed
        mock_create_user.return_value = _make_mock_user()
        mock_settings.lnbits_baseurl = "http://localhost:5000/"

        returned_arr = _make_arrangement(
            tpos_id=None,
            tpos_url=None,
            merchant_credentials="http://localhost:5000/wallet?usr=user_m1",
        )
        mock_create_arr.return_value = returned_arr

        data = _make_create_data()
        key_info = _make_key_info()

        # httpx should NOT be called, but we patch it to detect if it is
        with patch("orangepiller.views_api.httpx.AsyncClient") as mock_httpx_cls:
            result = await api_create_arrangement(data=data, key_info=key_info)

        # create_arrangement called with tpos fields as None
        call_kwargs = mock_create_arr.call_args[1]
        assert call_kwargs["tpos_id"] is None
        assert call_kwargs["tpos_url"] is None

        # merchant_credentials still populated
        assert call_kwargs["merchant_credentials"] == "http://localhost:5000/wallet?usr=user_m1"

        # httpx.AsyncClient was NOT called
        mock_httpx_cls.assert_not_called()

        # Warning present about TPoS not installed
        assert result.warning is not None
        assert "not installed" in result.warning.lower()

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_default_exts_omits_tpos_when_not_installed(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        """When TPoS absent, create_user_account is called with only orangepiller in default_exts."""
        from orangepiller.views_api import api_create_arrangement

        mock_get_ext.return_value = None
        mock_create_user.return_value = _make_mock_user()
        mock_settings.lnbits_baseurl = "http://localhost:5000/"
        mock_create_arr.return_value = _make_arrangement()

        data = _make_create_data()
        key_info = _make_key_info()

        with patch("orangepiller.views_api.httpx.AsyncClient"):
            await api_create_arrangement(data=data, key_info=key_info)

        mock_create_user.assert_called_once_with(default_exts=["orangepiller"])


class TestCreateArrangementTposHttpFailure:
    """TPoS installed but httpx fails → tpos_id=None, warning present, arrangement still created."""

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_create_arrangement_tpos_http_failure(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        from orangepiller.views_api import api_create_arrangement

        mock_get_ext.return_value = MagicMock()  # installed
        mock_create_user.return_value = _make_mock_user()
        mock_settings.lnbits_baseurl = "http://localhost:5000/"

        returned_arr = _make_arrangement(tpos_id=None, tpos_url=None)
        mock_create_arr.return_value = returned_arr

        # httpx raises HTTPError
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.HTTPError("Connection refused")
        mock_client_cm = MagicMock()
        mock_client_cm.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cm.__aexit__ = AsyncMock(return_value=False)

        data = _make_create_data()
        key_info = _make_key_info()

        with patch("orangepiller.views_api.httpx.AsyncClient", return_value=mock_client_cm):
            result = await api_create_arrangement(data=data, key_info=key_info)

        # Arrangement still created (not an exception)
        mock_create_arr.assert_called_once()
        call_kwargs = mock_create_arr.call_args[1]
        assert call_kwargs["tpos_id"] is None
        assert call_kwargs["tpos_url"] is None

        # Warning present with failure info
        assert result.warning is not None
        assert "failed" in result.warning.lower()


class TestMerchantCredentials:
    """Merchant credentials are always populated regardless of TPoS status."""

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_merchant_credentials_format_with_tpos(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        """merchant_credentials contains /wallet?usr={user_id} when TPoS installed."""
        from orangepiller.views_api import api_create_arrangement

        mock_get_ext.return_value = MagicMock()
        user = _make_mock_user(user_id="user_abc")
        mock_create_user.return_value = user
        mock_settings.lnbits_baseurl = "http://localhost:5000/"
        mock_create_arr.return_value = _make_arrangement()

        mock_response = _make_mock_httpx_response()
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cm = MagicMock()
        mock_client_cm.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cm.__aexit__ = AsyncMock(return_value=False)

        data = _make_create_data()
        key_info = _make_key_info()

        with patch("orangepiller.views_api.httpx.AsyncClient", return_value=mock_client_cm):
            await api_create_arrangement(data=data, key_info=key_info)

        call_kwargs = mock_create_arr.call_args[1]
        assert "/wallet?usr=user_abc" in call_kwargs["merchant_credentials"]

    @pytest.mark.anyio
    @patch(f"{_PATCH_PREFIX}.settings")
    @patch(f"{_PATCH_PREFIX}.create_arrangement", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.create_user_account_no_ckeck", new_callable=AsyncMock)
    @patch(f"{_PATCH_PREFIX}.get_installed_extension", new_callable=AsyncMock)
    async def test_merchant_credentials_format_without_tpos(
        self,
        mock_get_ext,
        mock_create_user,
        mock_create_arr,
        mock_settings,
    ):
        """merchant_credentials contains /wallet?usr={user_id} even when TPoS absent."""
        from orangepiller.views_api import api_create_arrangement

        mock_get_ext.return_value = None  # TPoS not installed
        user = _make_mock_user(user_id="user_xyz")
        mock_create_user.return_value = user
        mock_settings.lnbits_baseurl = "http://localhost:5000/"
        mock_create_arr.return_value = _make_arrangement()

        data = _make_create_data()
        key_info = _make_key_info()

        with patch("orangepiller.views_api.httpx.AsyncClient"):
            await api_create_arrangement(data=data, key_info=key_info)

        call_kwargs = mock_create_arr.call_args[1]
        assert "/wallet?usr=user_xyz" in call_kwargs["merchant_credentials"]


class TestExtendedCreateFields:
    """Verify CreateArrangement accepts all new M002 fields without validation error."""

    def test_extended_create_fields_accepted(self):
        """Construct CreateArrangement with all new fields — no ValidationError."""
        data = CreateArrangement(
            total_debt_sats=100000,
            reroute_percent=20,
            merchant_name="Bob's Bakery",
            currency="EUR",
            tip_options="[5,10,15]",
            tax_default=0.19,
            tax_inclusive=False,
            business_name="Bob GmbH",
            business_address="456 Elm St",
            business_vat_id="DE123456789",
        )
        assert data.merchant_name == "Bob's Bakery"
        assert data.currency == "EUR"
        assert data.tax_default == 0.19
        assert data.tax_inclusive is False
        assert data.business_name == "Bob GmbH"
        assert data.business_address == "456 Elm St"
        assert data.business_vat_id == "DE123456789"

    def test_extended_create_fields_defaults(self):
        """CreateArrangement with only required fields — new fields default gracefully."""
        data = CreateArrangement(
            total_debt_sats=50000,
            reroute_percent=10,
        )
        assert data.merchant_name is None
        assert data.currency == "sat"
        assert data.tip_options is None
        assert data.tax_default == 0
        assert data.tax_inclusive is True
        assert data.business_name is None
        assert data.business_address is None
        assert data.business_vat_id is None
