"""End-to-end tests against the real Ajax API.

Requires AJAX_EMAIL and AJAX_PASSWORD environment variables.
"""

from __future__ import annotations

import os

import pytest

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.spaces import SpacesApi

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("AJAX_EMAIL") or not os.environ.get("AJAX_PASSWORD"),
        reason="AJAX_EMAIL and AJAX_PASSWORD not set",
    ),
]


class TestRealConnection:
    @pytest.fixture
    async def client(self) -> AjaxGrpcClient:
        c = AjaxGrpcClient(email=os.environ["AJAX_EMAIL"], password=os.environ["AJAX_PASSWORD"])
        await c.connect()
        yield c
        await c.close()

    @pytest.mark.asyncio
    async def test_connect_and_list_spaces(self, client: AjaxGrpcClient) -> None:
        spaces_api = SpacesApi(client)
        spaces = await spaces_api.list_spaces()
        assert len(spaces) >= 0
