"""Spaces (hubs) API operations."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from custom_components.ajax_cobranded.api.models import Space
from custom_components.ajax_cobranded.const import ConnectionStatus, SecurityState

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

_FIND_SPACES_METHOD = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".find_user_spaces_with_pagination.FindUserSpacesWithPaginationService/execute"
)


class SpacesApi:
    """API operations for spaces (hubs)."""

    def __init__(self, client: AjaxGrpcClient) -> None:
        self._client = client

    @staticmethod
    def parse_space(proto_space: Any) -> Space:  # noqa: ANN401
        return Space(
            id=proto_space.id,
            hub_id=proto_space.hub_id if proto_space.hub_id else "",
            name=proto_space.profile.name,
            security_state=SecurityState(proto_space.security_state),
            connection_status=ConnectionStatus(proto_space.hub_connection_status),
            malfunctions_count=proto_space.malfunctions_count,
        )

    async def list_spaces(self) -> list[Space]:
        proto_path = str(Path(__file__).parent.parent / "proto")
        if proto_path not in sys.path:
            sys.path.append(proto_path)

        from v3.mobilegwsvc.service.find_user_spaces_with_pagination import (  # noqa: PLC0415
            endpoint_pb2_grpc,
            request_pb2,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = endpoint_pb2_grpc.FindUserSpacesWithPaginationServiceStub(channel)

        request = request_pb2.FindUserSpacesWithPaginationRequest(limit=100)
        response = await stub.execute(request, metadata=metadata, timeout=15)

        if response.HasField("failure"):
            _LOGGER.error("Failed to list spaces")
            return []

        return [self.parse_space(s) for s in response.success.spaces]
