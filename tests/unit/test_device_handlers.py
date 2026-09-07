"""Tests for device capability handlers."""

from __future__ import annotations

import pytest

from custom_components.aegis_ajax import device_handlers


def test_build_handler_map_rejects_duplicate_device_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Handler collisions must fail instead of silently changing capabilities."""
    handler = device_handlers.StaticDeviceHandler(("duplicate_type",), ())
    monkeypatch.setattr(device_handlers, "_HANDLERS", (handler, handler))

    with pytest.raises(
        ValueError, match="Duplicate device handler registration for 'duplicate_type'"
    ):
        device_handlers._build_handler_map()
