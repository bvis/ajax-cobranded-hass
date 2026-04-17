#!/usr/bin/env python3
"""Test the full Photo on Demand flow locally against the real Ajax API.

Usage:
    docker run --rm -v $(pwd):/app ajax-cobranded-dev python scripts/test_photo_flow.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.media import MediaApi

EMAIL = os.environ.get("AJAX_EMAIL", "")
PASSWORD_HASH = os.environ.get("AJAX_PASSWORD_HASH", "")
DEVICE_ID = os.environ.get("AJAX_DEVICE_ID", "")
APP_LABEL = os.environ.get("AJAX_APP_LABEL", "Ajax")
SPACE_ID = os.environ.get("AJAX_SPACE_ID", "")
HUB_ID = os.environ.get("AJAX_HUB_ID", "")
CAMERA_DEVICE_ID = "309F61FA"
CAMERA_DEVICE_TYPE = "motion_cam"

# Use a recent notification_id from the last capture
NOTIFICATION_ID = "484253666291560067864AD074A7AC6C2DF5E836309F61FA0000019D886931A9"


async def main() -> None:
    print(f"Connecting as {EMAIL}...")
    client = AjaxGrpcClient(
        email=EMAIL,
        password_hash=PASSWORD_HASH,
        device_id=DEVICE_ID,
        app_label=APP_LABEL,
    )
    await client.connect()
    await client.login()
    print(f"Logged in. Session: {client.session.user_hex_id}")

    media_api = MediaApi(client)
    devices_api = DevicesApi(client)

    # Step 1: Test streamNotificationMedia with the known notification_id
    print("\n=== Step 1: streamNotificationMedia with existing notification_id ===")
    print(f"notification_id: {NOTIFICATION_ID}")
    url = await media_api.get_photo_url(NOTIFICATION_ID, HUB_ID, timeout=10.0)
    print(f"Result: {url}")

    # Step 2: Trigger a new capture and try immediately
    print("\n=== Step 2: Trigger new capture ===")
    result = await devices_api.capture_photo(HUB_ID, CAMERA_DEVICE_ID, CAMERA_DEVICE_TYPE)
    print(f"Capture result: {result}")

    if result:
        print("Waiting 10s for push notification to arrive...")
        await asyncio.sleep(10)

        # We don't have FCM here, so use the notification_id from Step 1
        # In real flow, this would come from the push notification
        print("\n=== Step 3: streamNotificationMedia after capture ===")
        url2 = await media_api.get_photo_url(NOTIFICATION_ID, HUB_ID, timeout=15.0)
        print(f"Result: {url2}")

    await client.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
