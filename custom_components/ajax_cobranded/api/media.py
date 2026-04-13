"""Media API: retrieve photo URLs from notification media streams."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

_STREAM_NOTIFICATION_MEDIA = (
    "/systems.ajax.api.mobile.v2.notification.NotificationLogService/streamNotificationMedia"
)


def _encode_string_field(field_number: int, value: str) -> bytes:
    """Encode a protobuf string field (wire type 2)."""
    encoded = value.encode("utf-8")
    tag = (field_number << 3) | 2
    length_bytes = _encode_varint(len(encoded))
    return bytes([tag]) + length_bytes + encoded


def _encode_varint(value: int) -> bytes:
    """Encode an integer as a protobuf varint."""
    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def _encode_embedded_message(field_number: int, data: bytes) -> bytes:
    """Encode an embedded message field (wire type 2)."""
    tag = (field_number << 3) | 2
    length_bytes = _encode_varint(len(data))
    return bytes([tag]) + length_bytes + data


class MediaApi:
    """API for retrieving media (photos) from Ajax notification system."""

    def __init__(self, client: AjaxGrpcClient) -> None:
        self._client = client

    async def get_photo_url(
        self, notification_id: str, hub_hex_id: str, timeout: float = 15.0
    ) -> str | None:
        """Stream notification media and return the photo URL when ready.

        Opens a server-streaming gRPC call to NotificationLogService/streamNotificationMedia.
        Waits for IMAGE_STATUS_READY and extracts the photo URL.
        Returns None on timeout or if no URL is found.
        """
        # Build StreamNotificationMediaRequest:
        # field 1 (string): notification_id
        # field 2 (message): NotificationOriginId { field 1 (string): hub_hex_id }
        origin_msg = _encode_string_field(1, hub_hex_id)
        request_bytes = _encode_string_field(1, notification_id) + _encode_embedded_message(
            2, origin_msg
        )

        channel = self._client._get_channel()
        metadata = self._client._session.get_call_metadata()

        method = channel.unary_stream(
            _STREAM_NOTIFICATION_MEDIA,
            request_serializer=lambda x: x,
            response_deserializer=lambda x: x,
        )

        try:
            _LOGGER.debug(
                "Opening media stream: notification_id=%s hub=%s",
                notification_id[:20],
                hub_hex_id,
            )
            stream = method(request_bytes, metadata=metadata, timeout=timeout)
            async for raw_response in stream:
                # Search for HTTPS URLs in the response
                urls = re.findall(rb'https://[^\x00-\x1f\x7f-\x9f"\'\\]+', raw_response)
                for raw_url in urls:
                    url: str = raw_url.decode("utf-8", errors="ignore")
                    # Photo URLs can be on ajax.systems or S3 (hubs-uploaded-resources)
                    if ".ajax.systems" in url or "hubs-uploaded-resources" in url:
                        _LOGGER.debug("Photo URL from media stream: %s", url[:80])
                        return url
                _LOGGER.debug(
                    "Media stream frame: %d bytes, hex=%s",
                    len(raw_response),
                    raw_response[:200].hex(),
                )
        except TimeoutError:
            _LOGGER.debug("Timeout waiting for photo URL from media stream")
        except Exception:
            _LOGGER.debug("Error in notification media stream", exc_info=True)
        return None
