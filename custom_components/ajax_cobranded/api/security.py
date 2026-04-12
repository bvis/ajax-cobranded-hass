"""Security API operations (arm/disarm)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

_SERVICE_PREFIX = "/systems.ajax.api.mobile.v2.space.security.SpaceSecurityService"
_ARM_METHOD = f"{_SERVICE_PREFIX}/arm"
_DISARM_METHOD = f"{_SERVICE_PREFIX}/disarm"
_ARM_NIGHT_METHOD = f"{_SERVICE_PREFIX}/armToNightMode"
_DISARM_NIGHT_METHOD = f"{_SERVICE_PREFIX}/disarmFromNightMode"
_ARM_GROUP_METHOD = f"{_SERVICE_PREFIX}/armGroup"
_DISARM_GROUP_METHOD = f"{_SERVICE_PREFIX}/disarmGroup"


class SecurityError(Exception):
    """Raised when a security command fails."""


class SecurityApi:
    """API operations for arming/disarming."""

    def __init__(self, client: AjaxGrpcClient) -> None:
        self._client = client

    def _get_proto_path(self) -> str:
        proto_path = str(Path(__file__).parent.parent / "proto")
        if proto_path not in sys.path:
            sys.path.append(proto_path)
        return proto_path

    async def arm(self, space_id: str, ignore_alarms: bool = False) -> None:
        self._get_proto_path()
        from systems.ajax.api.mobile.v2.common.space import space_locator_pb2  # noqa: PLC0415
        from systems.ajax.api.mobile.v2.space.security import (  # noqa: PLC0415
            arm_request_pb2,
            space_security_endpoints_pb2_grpc,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = space_security_endpoints_pb2_grpc.SpaceSecurityServiceStub(channel)

        request = arm_request_pb2.ArmSpaceRequest(
            space_locator=space_locator_pb2.SpaceLocator(space_id=space_id),
            ignore_alarms=ignore_alarms,
        )
        response = await stub.arm(request, metadata=metadata, timeout=15)
        if response.HasField("failure"):
            raise SecurityError("Arm command rejected by server")
        _LOGGER.debug("Armed space %s", space_id)

    async def disarm(self, space_id: str) -> None:
        self._get_proto_path()
        from systems.ajax.api.mobile.v2.common.space import space_locator_pb2  # noqa: PLC0415
        from systems.ajax.api.mobile.v2.space.security import (  # noqa: PLC0415
            disarm_request_pb2,
            space_security_endpoints_pb2_grpc,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = space_security_endpoints_pb2_grpc.SpaceSecurityServiceStub(channel)

        request = disarm_request_pb2.DisarmSpaceRequest(
            space_locator=space_locator_pb2.SpaceLocator(space_id=space_id),
        )
        response = await stub.disarm(request, metadata=metadata, timeout=15)
        if response.HasField("failure"):
            raise SecurityError("Disarm command rejected by server")
        _LOGGER.debug("Disarmed space %s", space_id)

    async def arm_night_mode(self, space_id: str, ignore_alarms: bool = False) -> None:
        self._get_proto_path()
        from systems.ajax.api.mobile.v2.common.space import space_locator_pb2  # noqa: PLC0415
        from systems.ajax.api.mobile.v2.space.security import (  # noqa: PLC0415
            arm_to_night_mode_request_pb2,
            space_security_endpoints_pb2_grpc,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = space_security_endpoints_pb2_grpc.SpaceSecurityServiceStub(channel)

        request = arm_to_night_mode_request_pb2.ArmSpaceToNightModeRequest(
            space_locator=space_locator_pb2.SpaceLocator(space_id=space_id),
            ignore_alarms=ignore_alarms,
        )
        response = await stub.armToNightMode(request, metadata=metadata, timeout=15)
        if response.HasField("failure"):
            raise SecurityError("Arm to night mode command rejected by server")
        _LOGGER.debug("Armed space %s in night mode", space_id)

    async def arm_group(self, space_id: str, group_id: str, ignore_alarms: bool = False) -> None:
        self._get_proto_path()
        from systems.ajax.api.mobile.v2.common.space import space_locator_pb2  # noqa: PLC0415
        from systems.ajax.api.mobile.v2.space.security import (  # noqa: PLC0415
            space_security_endpoints_pb2_grpc,
        )
        from systems.ajax.api.mobile.v2.space.security.group import (  # noqa: PLC0415
            arm_group_request_pb2,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = space_security_endpoints_pb2_grpc.SpaceSecurityServiceStub(channel)

        request = arm_group_request_pb2.ArmGroupRequest(
            space_locator=space_locator_pb2.SpaceLocator(space_id=space_id),
            group_id=group_id,
            ignore_alarms=ignore_alarms,
        )
        response = await stub.armGroup(request, metadata=metadata, timeout=15)
        if response.HasField("failure"):
            raise SecurityError("Arm group command rejected by server")
        _LOGGER.debug("Armed group %s in space %s", group_id, space_id)

    async def disarm_group(self, space_id: str, group_id: str) -> None:
        self._get_proto_path()
        from systems.ajax.api.mobile.v2.common.space import space_locator_pb2  # noqa: PLC0415
        from systems.ajax.api.mobile.v2.space.security import (  # noqa: PLC0415
            space_security_endpoints_pb2_grpc,
        )
        from systems.ajax.api.mobile.v2.space.security.group import (  # noqa: PLC0415
            disarm_group_request_pb2,
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()
        stub = space_security_endpoints_pb2_grpc.SpaceSecurityServiceStub(channel)

        request = disarm_group_request_pb2.DisarmGroupRequest(
            space_locator=space_locator_pb2.SpaceLocator(space_id=space_id),
            group_id=group_id,
        )
        response = await stub.disarmGroup(request, metadata=metadata, timeout=15)
        if response.HasField("failure"):
            raise SecurityError("Disarm group command rejected by server")
        _LOGGER.debug("Disarmed group %s in space %s", group_id, space_id)
