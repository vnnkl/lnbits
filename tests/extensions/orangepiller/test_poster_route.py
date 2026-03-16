"""Tests for the printable poster route (S02/T02)."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from orangepiller.models import Arrangement


def _make_arrangement(**overrides) -> Arrangement:
    defaults = dict(
        id="arr_poster",
        orange_piller_wallet="wallet_op",
        merchant_wallet="wallet_merchant",
        merchant_user_id="user_merchant",
        total_debt_sats=10000,
        repaid_sats=0,
        reroute_percent=50,
        status="active",
        tpos_url="https://lnbits.example.com/tpos/abc123",
        merchant_name="Coffee Shop",
    )
    defaults.update(overrides)
    return Arrangement(**defaults)


class TestPosterRoute:
    """GET /orangepiller/poster/{arrangement_id} route tests."""

    @pytest.mark.anyio
    @patch("orangepiller.views.get_arrangement", new_callable=AsyncMock)
    async def test_poster_route_valid_arrangement(self, mock_get):
        """Valid arrangement with tpos_url → 200, contains merchant name and qrcode."""
        from orangepiller.views import poster
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        arr = _make_arrangement()
        mock_get.return_value = arr

        # Build a minimal FastAPI app to test the route
        app = FastAPI()
        app.get("/poster/{arrangement_id}")(poster)
        client = TestClient(app)

        response = client.get("/poster/arr_poster")
        assert response.status_code == 200
        body = response.text
        assert "Coffee Shop" in body
        assert "qrcode" in body.lower() or "lnbits-qrcode" in body

    @pytest.mark.anyio
    @patch("orangepiller.views.get_arrangement", new_callable=AsyncMock)
    async def test_poster_route_missing_arrangement(self, mock_get):
        """Missing arrangement → 404."""
        from orangepiller.views import poster
        from unittest.mock import MagicMock

        mock_get.return_value = None

        request = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await poster(request, "nonexistent_id")
        assert exc_info.value.status_code == 404

    @pytest.mark.anyio
    @patch("orangepiller.views.get_arrangement", new_callable=AsyncMock)
    async def test_poster_route_no_tpos_url(self, mock_get):
        """Arrangement exists but tpos_url is None → 404."""
        from orangepiller.views import poster
        from unittest.mock import MagicMock

        arr = _make_arrangement(tpos_url=None)
        mock_get.return_value = arr

        request = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await poster(request, "arr_poster")
        assert exc_info.value.status_code == 404
