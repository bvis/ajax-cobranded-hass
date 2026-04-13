"""Tests for photo storage."""

from __future__ import annotations

from custom_components.ajax_cobranded.photo_storage import _overlay_timestamp, _sanitize_name


class TestSanitizeName:
    def test_simple_name(self) -> None:
        # Accented characters are alphanumeric in Python (isalnum() returns True)
        assert _sanitize_name("PASSADÍS") == "PASSADÍS"

    def test_name_with_spaces(self) -> None:
        assert _sanitize_name("Front Door") == "Front Door"

    def test_name_with_special_chars(self) -> None:
        result = _sanitize_name("Device <1> / test")
        assert "<" not in result
        assert "/" not in result


class TestOverlayTimestamp:
    def test_overlay_returns_bytes(self) -> None:
        # Create a minimal JPEG-like image using Pillow
        import io

        from PIL import Image

        img = Image.new("RGB", (320, 240), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        original = buf.getvalue()

        result = _overlay_timestamp(original)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_overlay_on_invalid_image_returns_original(self) -> None:
        original = b"not a real image"
        result = _overlay_timestamp(original)
        assert result == original
