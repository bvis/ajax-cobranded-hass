"""Tests for spaces API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.models import Space
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import ConnectionStatus, SecurityState

_FIND_SPACES_BASE = "v3.mobilegwsvc.service.find_user_spaces_with_pagination"


class TestParseSpace:
    def test_parse_space_from_proto(self) -> None:
        proto_space = MagicMock()
        proto_space.id = "space-abc"
        proto_space.hub_id = "hub-xyz"
        proto_space.profile.name = "My Home"
        proto_space.security_state = 2  # DISARMED
        proto_space.hub_connection_status = 1  # ONLINE
        proto_space.malfunctions_count = 0

        result = SpacesApi.parse_space(proto_space)
        assert isinstance(result, Space)
        assert result.id == "space-abc"
        assert result.hub_id == "hub-xyz"
        assert result.name == "My Home"
        assert result.security_state == SecurityState.DISARMED
        assert result.connection_status == ConnectionStatus.ONLINE

    def test_parse_space_armed(self) -> None:
        proto_space = MagicMock()
        proto_space.id = "s1"
        proto_space.hub_id = "h1"
        proto_space.profile.name = "Office"
        proto_space.security_state = 1  # ARMED
        proto_space.hub_connection_status = 1
        proto_space.malfunctions_count = 2

        result = SpacesApi.parse_space(proto_space)
        assert result.security_state == SecurityState.ARMED
        assert result.malfunctions_count == 2

    def test_parse_space_hub_id_optional(self) -> None:
        proto_space = MagicMock()
        proto_space.id = "s1"
        proto_space.hub_id = ""
        proto_space.profile.name = "Test"
        proto_space.security_state = 0
        proto_space.hub_connection_status = 0
        proto_space.malfunctions_count = 0

        result = SpacesApi.parse_space(proto_space)
        assert result.hub_id == ""


class TestListSpaces:
    @pytest.mark.asyncio
    async def test_list_spaces_success(self) -> None:
        mock_client = MagicMock()
        mock_channel = MagicMock()
        mock_client._get_channel.return_value = mock_channel
        mock_client._session.get_call_metadata.return_value = [("token", "abc")]

        api = SpacesApi(mock_client)

        # Build mock spaces
        mock_space = MagicMock()
        mock_space.id = "space-1"
        mock_space.hub_id = "hub-1"
        mock_space.profile.name = "Home"
        mock_space.security_state = 2
        mock_space.hub_connection_status = 1
        mock_space.malfunctions_count = 0

        mock_response = MagicMock()
        mock_response.HasField.return_value = False
        mock_response.success.spaces = [mock_space]

        mock_stub_instance = MagicMock()
        mock_stub_instance.execute = AsyncMock(return_value=mock_response)
        mock_stub_class = MagicMock(return_value=mock_stub_instance)

        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(FindUserSpacesWithPaginationServiceStub=mock_stub_class)

        with patch.dict(
            "sys.modules",
            {
                f"{_FIND_SPACES_BASE}.endpoint_pb2_grpc": mock_grpc_module,
                f"{_FIND_SPACES_BASE}.request_pb2": mock_request_pb2,
                _FIND_SPACES_BASE: MagicMock(
                    endpoint_pb2_grpc=mock_grpc_module,
                    request_pb2=mock_request_pb2,
                ),
            },
        ):
            spaces = await api.list_spaces()

        assert len(spaces) == 1
        assert spaces[0].id == "space-1"

    @pytest.mark.asyncio
    async def test_list_spaces_failure_returns_empty(self) -> None:
        mock_client = MagicMock()
        mock_channel = MagicMock()
        mock_client._get_channel.return_value = mock_channel
        mock_client._session.get_call_metadata.return_value = []

        api = SpacesApi(mock_client)

        mock_response = MagicMock()
        mock_response.HasField.return_value = True  # has failure

        mock_stub_instance = MagicMock()
        mock_stub_instance.execute = AsyncMock(return_value=mock_response)
        mock_stub_class = MagicMock(return_value=mock_stub_instance)

        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(FindUserSpacesWithPaginationServiceStub=mock_stub_class)

        with patch.dict(
            "sys.modules",
            {
                f"{_FIND_SPACES_BASE}.endpoint_pb2_grpc": mock_grpc_module,
                f"{_FIND_SPACES_BASE}.request_pb2": mock_request_pb2,
                _FIND_SPACES_BASE: MagicMock(
                    endpoint_pb2_grpc=mock_grpc_module,
                    request_pb2=mock_request_pb2,
                ),
            },
        ):
            spaces = await api.list_spaces()

        assert spaces == []
