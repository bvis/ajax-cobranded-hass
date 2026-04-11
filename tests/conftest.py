"""Shared test fixtures."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_grpc_channel() -> MagicMock:
    """Create a mock gRPC channel."""
    channel = MagicMock()
    channel.close = AsyncMock()
    return channel


@pytest.fixture
def mock_session_token() -> bytes:
    """A fake session token (16 bytes)."""
    return bytes.fromhex("aabbccdd11223344aabbccdd11223344")


@pytest.fixture
def mock_user_hex_id() -> str:
    return "user123hex"
