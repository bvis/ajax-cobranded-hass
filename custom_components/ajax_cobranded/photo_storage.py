"""Photo storage with timestamp overlay for Ajax Security."""

from __future__ import annotations

import asyncio
import io
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PHOTOS_BASE_DIR = "ajax_photos"


def _sanitize_name(name: str) -> str:
    """Sanitize device name for use as directory name."""
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()


def _overlay_timestamp(image_bytes: bytes) -> bytes:
    """Add timestamp overlay on the photo."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415

        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        font = ImageFont.load_default(size=11)

        text_bbox = draw.textbbox((0, 0), now, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        padding = 2
        x = img.width - text_w - padding * 2 - 4
        y = img.height - text_h - padding * 2 - 4
        draw.rectangle(
            [(x, y), (x + text_w + padding * 2, y + text_h + padding * 2)],
            fill=(0, 0, 0, 160),
        )
        draw.text((x + padding, y + padding), now, fill=(255, 255, 255, 255), font=font)
        img = Image.alpha_composite(img, overlay).convert("RGB")

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90)
        return output.getvalue()
    except Exception:
        _LOGGER.debug("Failed to overlay timestamp, returning original image")
        return image_bytes


async def save_photo(
    hass: HomeAssistant,
    image_bytes: bytes,
    device_id: str,
    device_name: str,
) -> Path | None:
    """Save photo with timestamp overlay to media directory."""

    def _do_save() -> Path | None:
        try:
            media_dir = Path(hass.config.media_dirs.get("local", "/media"))
            device_dir = media_dir / PHOTOS_BASE_DIR / _sanitize_name(device_name)
            device_dir.mkdir(parents=True, exist_ok=True)

            stamped = _overlay_timestamp(image_bytes)
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
            filepath = device_dir / filename
            filepath.write_bytes(stamped)
            _LOGGER.debug("Photo saved: %s (%d bytes)", filepath, len(stamped))

            # Also save as "last.jpg" for camera entity persistence
            last_path = device_dir / "last.jpg"
            last_path.write_bytes(stamped)

            return filepath
        except Exception:
            _LOGGER.exception("Failed to save photo")
            return None

    return await asyncio.to_thread(_do_save)


async def load_last_photo(
    hass: HomeAssistant,
    device_name: str,
) -> bytes | None:
    """Load the last saved photo for a device."""

    def _do_load() -> bytes | None:
        try:
            media_dir = Path(hass.config.media_dirs.get("local", "/media"))
            last_path = media_dir / PHOTOS_BASE_DIR / _sanitize_name(device_name) / "last.jpg"
            if last_path.exists():
                return last_path.read_bytes()
        except Exception:
            _LOGGER.debug("Failed to load last photo")
        return None

    return await asyncio.to_thread(_do_load)


async def cleanup_old_photos(
    hass: HomeAssistant,
    retention_days: int = 30,
    max_photos_per_device: int = 100,
) -> list[str]:
    """Delete photos older than retention period or exceeding max count per device."""

    def _do_cleanup() -> list[str]:
        deleted: list[str] = []
        try:
            media_dir = Path(hass.config.media_dirs.get("local", "/media"))
            photos_dir = media_dir / PHOTOS_BASE_DIR
            if not photos_dir.exists():
                return deleted

            cutoff = time.time() - (retention_days * 86400)

            for device_dir in photos_dir.iterdir():
                if not device_dir.is_dir():
                    continue

                # Get all jpg files except last.jpg, sorted by mtime (newest first)
                photos = sorted(
                    [
                        f
                        for f in device_dir.iterdir()
                        if f.is_file() and f.suffix == ".jpg" and f.name != "last.jpg"
                    ],
                    key=lambda f: f.stat().st_mtime,
                    reverse=True,
                )

                for i, photo in enumerate(photos):
                    should_delete = False
                    # Delete by age
                    if photo.stat().st_mtime < cutoff:
                        should_delete = True
                    # Delete by count (keep max_photos_per_device newest)
                    if max_photos_per_device > 0 and i >= max_photos_per_device:
                        should_delete = True

                    if should_delete:
                        photo.unlink()
                        deleted.append(str(photo))

        except Exception:
            _LOGGER.exception("Error cleaning up old photos")
        return deleted

    return await asyncio.to_thread(_do_cleanup)
