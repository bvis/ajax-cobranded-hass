"""Tests for security API (arm/disarm)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.security import SecurityApi, SecurityError

_GRPC_MOD = "systems.ajax.api.mobile.v2.space.security.space_security_endpoints_pb2_grpc"


class TestSecurityApiInit:
    def test_init(self) -> None:
        client = MagicMock()
        api = SecurityApi(client)
        assert api._client is client


class TestGetProtoPath:
    def test_get_proto_path_adds_to_sys_path(self) -> None:
        import sys

        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        path = api._get_proto_path()
        assert path in sys.path
        assert path.endswith("proto")


def _make_security_api() -> tuple[SecurityApi, MagicMock, MagicMock]:
    """Return (api, mock_channel, mock_stub)."""
    mock_client = MagicMock()
    mock_channel = MagicMock()
    mock_client._get_channel.return_value = mock_channel
    mock_client._session.get_call_metadata.return_value = [("token", "abc")]
    api = SecurityApi(mock_client)
    return api, mock_channel, MagicMock()


class TestArm:
    @pytest.mark.asyncio
    async def test_arm_calls_stub(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = False
        mock_stub_instance.arm = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_arm_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "systems.ajax.api.mobile.v2.space.security.arm_request_pb2": mock_arm_request_pb2,
                _GRPC_MOD: mock_grpc_module,
                "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                "systems.ajax.api.mobile.v2.space.security": MagicMock(
                    arm_request_pb2=mock_arm_request_pb2,
                    space_security_endpoints_pb2_grpc=mock_grpc_module,
                ),
                "systems.ajax.api.mobile.v2.common.space": MagicMock(
                    space_locator_pb2=mock_locator_pb2,
                ),
            },
        ):
            await api.arm("space-1")

        mock_stub_instance.arm.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_raises_on_failure(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = True
        mock_stub_instance.arm = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_arm_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "systems.ajax.api.mobile.v2.space.security.arm_request_pb2": (
                        mock_arm_request_pb2
                    ),
                    _GRPC_MOD: mock_grpc_module,
                    "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                    "systems.ajax.api.mobile.v2.space.security": MagicMock(
                        arm_request_pb2=mock_arm_request_pb2,
                        space_security_endpoints_pb2_grpc=mock_grpc_module,
                    ),
                    "systems.ajax.api.mobile.v2.common.space": MagicMock(
                        space_locator_pb2=mock_locator_pb2,
                    ),
                },
            ),
            pytest.raises(SecurityError, match="Arm command rejected"),
        ):
            await api.arm("space-1")


class TestDisarm:
    @pytest.mark.asyncio
    async def test_disarm_calls_stub(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = False
        mock_stub_instance.disarm = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_disarm_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "systems.ajax.api.mobile.v2.space.security.disarm_request_pb2": (
                    mock_disarm_request_pb2
                ),
                _GRPC_MOD: mock_grpc_module,
                "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                "systems.ajax.api.mobile.v2.space.security": MagicMock(
                    disarm_request_pb2=mock_disarm_request_pb2,
                    space_security_endpoints_pb2_grpc=mock_grpc_module,
                ),
                "systems.ajax.api.mobile.v2.common.space": MagicMock(
                    space_locator_pb2=mock_locator_pb2,
                ),
            },
        ):
            await api.disarm("space-1")

        mock_stub_instance.disarm.assert_called_once()

    @pytest.mark.asyncio
    async def test_disarm_raises_on_failure(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = True
        mock_stub_instance.disarm = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_disarm_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "systems.ajax.api.mobile.v2.space.security.disarm_request_pb2": (
                        mock_disarm_request_pb2
                    ),
                    _GRPC_MOD: mock_grpc_module,
                    "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                    "systems.ajax.api.mobile.v2.space.security": MagicMock(
                        disarm_request_pb2=mock_disarm_request_pb2,
                        space_security_endpoints_pb2_grpc=mock_grpc_module,
                    ),
                    "systems.ajax.api.mobile.v2.common.space": MagicMock(
                        space_locator_pb2=mock_locator_pb2,
                    ),
                },
            ),
            pytest.raises(SecurityError, match="Disarm command rejected"),
        ):
            await api.disarm("space-1")


class TestArmNightMode:
    @pytest.mark.asyncio
    async def test_arm_night_mode_calls_stub(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = False
        mock_stub_instance.armToNightMode = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "systems.ajax.api.mobile.v2.space.security.arm_to_night_mode_request_pb2": (
                    mock_request_pb2
                ),
                _GRPC_MOD: mock_grpc_module,
                "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                "systems.ajax.api.mobile.v2.space.security": MagicMock(
                    arm_to_night_mode_request_pb2=mock_request_pb2,
                    space_security_endpoints_pb2_grpc=mock_grpc_module,
                ),
                "systems.ajax.api.mobile.v2.common.space": MagicMock(
                    space_locator_pb2=mock_locator_pb2,
                ),
            },
        ):
            await api.arm_night_mode("space-1")

        mock_stub_instance.armToNightMode.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_night_mode_raises_on_failure(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = True
        mock_stub_instance.armToNightMode = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "systems.ajax.api.mobile.v2.space.security.arm_to_night_mode_request_pb2": (
                        mock_request_pb2
                    ),
                    _GRPC_MOD: mock_grpc_module,
                    "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                    "systems.ajax.api.mobile.v2.space.security": MagicMock(
                        arm_to_night_mode_request_pb2=mock_request_pb2,
                        space_security_endpoints_pb2_grpc=mock_grpc_module,
                    ),
                    "systems.ajax.api.mobile.v2.common.space": MagicMock(
                        space_locator_pb2=mock_locator_pb2,
                    ),
                },
            ),
            pytest.raises(SecurityError, match="night mode command rejected"),
        ):
            await api.arm_night_mode("space-1")


class TestArmGroup:
    @pytest.mark.asyncio
    async def test_arm_group_calls_stub(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = False
        mock_stub_instance.armGroup = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_arm_group_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "systems.ajax.api.mobile.v2.space.security.group.arm_group_request_pb2": (
                    mock_arm_group_request_pb2
                ),
                _GRPC_MOD: mock_grpc_module,
                "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                "systems.ajax.api.mobile.v2.space.security.group": MagicMock(
                    arm_group_request_pb2=mock_arm_group_request_pb2,
                ),
                "systems.ajax.api.mobile.v2.space.security": MagicMock(
                    space_security_endpoints_pb2_grpc=mock_grpc_module,
                ),
                "systems.ajax.api.mobile.v2.common.space": MagicMock(
                    space_locator_pb2=mock_locator_pb2,
                ),
            },
        ):
            await api.arm_group("space-1", "group-1")

        mock_stub_instance.armGroup.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_group_raises_on_failure(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = True
        mock_stub_instance.armGroup = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_arm_group_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "systems.ajax.api.mobile.v2.space.security.group.arm_group_request_pb2": (
                        mock_arm_group_request_pb2
                    ),
                    _GRPC_MOD: mock_grpc_module,
                    "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                    "systems.ajax.api.mobile.v2.space.security.group": MagicMock(
                        arm_group_request_pb2=mock_arm_group_request_pb2,
                    ),
                    "systems.ajax.api.mobile.v2.space.security": MagicMock(
                        space_security_endpoints_pb2_grpc=mock_grpc_module,
                    ),
                    "systems.ajax.api.mobile.v2.common.space": MagicMock(
                        space_locator_pb2=mock_locator_pb2,
                    ),
                },
            ),
            pytest.raises(SecurityError, match="Arm group command rejected"),
        ):
            await api.arm_group("space-1", "group-1")


class TestDisarmGroup:
    @pytest.mark.asyncio
    async def test_disarm_group_calls_stub(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = False
        mock_stub_instance.disarmGroup = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_disarm_group_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "systems.ajax.api.mobile.v2.space.security.group.disarm_group_request_pb2": (
                    mock_disarm_group_request_pb2
                ),
                _GRPC_MOD: mock_grpc_module,
                "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                "systems.ajax.api.mobile.v2.space.security.group": MagicMock(
                    disarm_group_request_pb2=mock_disarm_group_request_pb2,
                ),
                "systems.ajax.api.mobile.v2.space.security": MagicMock(
                    space_security_endpoints_pb2_grpc=mock_grpc_module,
                ),
                "systems.ajax.api.mobile.v2.common.space": MagicMock(
                    space_locator_pb2=mock_locator_pb2,
                ),
            },
        ):
            await api.disarm_group("space-1", "group-1")

        mock_stub_instance.disarmGroup.assert_called_once()

    @pytest.mark.asyncio
    async def test_disarm_group_raises_on_failure(self) -> None:
        api, mock_channel, _ = _make_security_api()

        mock_stub_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.HasField.return_value = True
        mock_stub_instance.disarmGroup = AsyncMock(return_value=mock_response)

        mock_stub_class = MagicMock(return_value=mock_stub_instance)
        mock_disarm_group_request_pb2 = MagicMock()
        mock_grpc_module = MagicMock(SpaceSecurityServiceStub=mock_stub_class)
        mock_locator_pb2 = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "systems.ajax.api.mobile.v2.space.security.group.disarm_group_request_pb2": (
                        mock_disarm_group_request_pb2
                    ),
                    _GRPC_MOD: mock_grpc_module,
                    "systems.ajax.api.mobile.v2.common.space.space_locator_pb2": mock_locator_pb2,
                    "systems.ajax.api.mobile.v2.space.security.group": MagicMock(
                        disarm_group_request_pb2=mock_disarm_group_request_pb2,
                    ),
                    "systems.ajax.api.mobile.v2.space.security": MagicMock(
                        space_security_endpoints_pb2_grpc=mock_grpc_module,
                    ),
                    "systems.ajax.api.mobile.v2.common.space": MagicMock(
                        space_locator_pb2=mock_locator_pb2,
                    ),
                },
            ),
            pytest.raises(SecurityError, match="Disarm group command rejected"),
        ):
            await api.disarm_group("space-1", "group-1")


class TestArmingCommands:
    def test_arm_is_callable(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        assert callable(api.arm)

    def test_disarm_is_callable(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        assert callable(api.disarm)

    def test_arm_night_mode_is_callable(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        assert callable(api.arm_night_mode)

    def test_arm_group_is_callable(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        assert callable(api.arm_group)

    def test_disarm_group_is_callable(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        assert callable(api.disarm_group)
