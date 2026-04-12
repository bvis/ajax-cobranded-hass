#!/usr/bin/env python3
"""Interactive CLI to test Ajax gRPC connection against the real system.

Usage:
    AJAX_EMAIL=your@email.com AJAX_PASSWORD=yourpass python scripts/test_connection.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.security import SecurityApi
from custom_components.ajax_cobranded.api.spaces import SpacesApi


async def main() -> None:
    email = os.environ.get("AJAX_EMAIL")
    password = os.environ.get("AJAX_PASSWORD")
    if not email or not password:
        print("Error: Set AJAX_EMAIL and AJAX_PASSWORD environment variables.")
        sys.exit(1)

    print(f"Connecting as {email}...")
    client = AjaxGrpcClient(email=email, password=password)
    await client.connect()

    try:
        print("Connected to mobile-gw.prod.ajax.systems:443")
        spaces_api = SpacesApi(client)
        spaces = await spaces_api.list_spaces()

        print(f"\nFound {len(spaces)} space(s):")
        for space in spaces:
            print(f"  [{space.id}] {space.name}")
            print(f"    Hub: {space.hub_id}")
            print(f"    State: {space.security_state.name}")
            print(f"    Online: {space.is_online}")
            print(f"    Malfunctions: {space.malfunctions_count}")

        if spaces:
            print("\nCommands:")
            print("  arm <space_id>    - Arm a space")
            print("  disarm <space_id> - Disarm a space")
            print("  night <space_id>  - Night mode")
            print("  quit              - Exit")

            security_api = SecurityApi(client)

            while True:
                try:
                    cmd = input("\n> ").strip().split()
                except (EOFError, KeyboardInterrupt):
                    break
                if not cmd or cmd[0] == "quit":
                    break
                if len(cmd) < 2:
                    print("Usage: <command> <space_id>")
                    continue
                action, space_id = cmd[0], cmd[1]
                try:
                    if action == "arm":
                        await security_api.arm(space_id)
                        print("Armed.")
                    elif action == "disarm":
                        await security_api.disarm(space_id)
                        print("Disarmed.")
                    elif action == "night":
                        await security_api.arm_night_mode(space_id)
                        print("Night mode.")
                    else:
                        print(f"Unknown command: {action}")
                except Exception as e:
                    print(f"Error: {e}")
    finally:
        await client.close()
        print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(main())
