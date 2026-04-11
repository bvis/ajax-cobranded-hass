# Ajax Security Home Assistant Integration — Design Spec

## Overview

A Home Assistant custom integration for Ajax Security Systems (Protegim and any co-branded Ajax app). Communicates with the Ajax cloud backend via **gRPC** — the same protocol the official mobile app uses — requiring only standard user credentials (email + password). No Enterprise API key needed.

## Context

### What is Protegim?

Protegim ("Protegim, l'alarma catalana") is a Catalan security brand operated by ISP Seguretat SLU. It uses Ajax Systems hardware. The Protegim app (`com.ajaxsystems.protegim`) is a co-branded version of the main Ajax Security System app — same backend (`mobile-gw.prod.ajax.systems:443`), same protocol, same authentication.

### Why gRPC?

Decompilation of the Protegim Android APK (v3.30) revealed:

- The mobile app communicates **exclusively via gRPC with Protobuf** (not the REST Enterprise API)
- **No API key required** — authentication is purely email + SHA-256(password)
- **No SSL pinning** — production servers use public CAs
- **Server-side streaming** available for real-time device updates
- ~225 gRPC services exposed on the mobile gateway

Existing HA integrations (foXaCe, exabird) use the REST Enterprise API which requires an API key that Ajax only issues to large security companies. This integration bypasses that limitation entirely.

### gRPC Server

```
Host: mobile-gw.prod.ajax.systems
Port: 443 (TLS, public CAs)
Protocol: gRPC + Protobuf (proto3)
```

---

## Architecture

### Project Structure

```
ajax-cobranded-hass/
├── custom_components/
│   └── ajax_cobranded/
│       ├── __init__.py              # HA integration setup
│       ├── manifest.json            # HACS/HA metadata
│       ├── config_flow.py           # Configuration UI (email/password/2FA)
│       ├── const.py                 # Constants
│       ├── coordinator.py           # DataUpdateCoordinator (orchestrates polling + streams)
│       ├── api/                     # Pure gRPC client (no HA dependency)
│       │   ├── __init__.py
│       │   ├── client.py            # AjaxGrpcClient — auth, session, channel
│       │   ├── session.py           # Session management (login, refresh, 2FA)
│       │   ├── spaces.py            # Space/hub operations
│       │   ├── devices.py           # Device streaming and commands
│       │   ├── security.py          # Arm/disarm/night mode
│       │   └── models.py            # Python dataclasses (mapping from protos)
│       ├── proto/                   # Compiled protos (*_pb2.py, *_pb2_grpc.py)
│       ├── alarm_control_panel.py   # HA entity: alarm panel
│       ├── binary_sensor.py         # HA entity: binary sensors
│       ├── sensor.py                # HA entity: numeric/diagnostic sensors
│       ├── switch.py                # HA entity: relays/switches
│       ├── light.py                 # HA entity: dimmers
│       ├── strings.json             # EN translations
│       └── translations/
│           ├── es.json
│           └── ca.json              # Catalan (Protegim's primary market)
├── tests/
│   ├── unit/
│   ├── e2e/
│   └── conftest.py
├── scripts/
│   ├── test_connection.py           # Interactive test against real system
│   └── compile_protos.sh            # Proto compiler script
├── proto_src/                       # Source .proto files (extracted from APK)
├── Dockerfile.dev
├── Makefile
├── pyproject.toml
└── .pre-commit-config.yaml
```

### Separation of Concerns

- **`api/`**: Pure Python gRPC client. Zero HA dependencies. Testable and usable as a standalone library.
- **`coordinator.py`**: Bridge between the API layer and HA entities. Manages data refresh lifecycle.
- **Entity files**: Thin mapping from coordinator data to HA entity states. Minimal logic.
- **`proto/`**: Auto-generated from `proto_src/`. Never hand-edited.

---

## gRPC Client and Session Management

### Connection

A single `grpc.aio.secure_channel` to `mobile-gw.prod.ajax.systems:443` with default TLS credentials (public CAs). All calls pass through two client interceptors that replicate the mobile app:

**Session Interceptor** — injects on every call:
- `client-session-token`: hex-encoded session_token
- `a911-user-id`: user_hex_id from LiteAccount

**Device Info Interceptor** — injects:
- `client-os`: `"Android"`
- `client-version-major`: `"3.30"`
- `application-label`: `"Protegim"`
- `client-device-type`: `"MOBILE"`
- `client-device-id`: UUID generated once and persisted
- `client-app-type`: `"USER"`

### Authentication Flow

```
1. LoginByPasswordService.execute(email, SHA256(password), USER_ROLE_USER)
   ├── Success → session_token (bytes→hex) + LiteAccount
   └── TwoFactorAuthRequiredError → request_id
       └── 2. LoginByTotpService.execute(email, USER_ROLE_USER, totp_code, request_id)
           └── Success → session_token + LiteAccount

3. Refresh: LoginByAuthTokenService.execute(session_token) every ~13 min
   ├── Success → new session_token
   └── Failure → full re-login
```

### Retry with Backoff

Every gRPC call goes through a wrapper with:
- **3 retries** on transient errors (`UNAVAILABLE`, `DEADLINE_EXCEEDED`, `INTERNAL`)
- **Exponential backoff**: 1s, 2s, 4s (with ±20% jitter)
- **Client-side rate limiting**: max 60 requests / 60s window
- **Per-call timeout**: 10s default, 30s for streams

### Session Persistence

`session_token` and `device_id` are persisted in HA's `config_entry.data` to survive restarts. On startup, `LoginByAuthToken` is attempted first; full re-login only if that fails.

---

## Home Assistant Entities

### Alarm Control Panel (1 per space/hub)

| Attribute | Source |
|---|---|
| State | `LiteSpace.security_state` → ARMED/DISARMED/ARMED_NIGHT/ARMED_CUSTOM_BYPASS |
| Arm Away | `SpaceSecurityService.arm(space_id, ignore_alarms=False)` |
| Arm Night | `SpaceSecurityService.armToNightMode(space_id)` |
| Disarm | `SpaceSecurityService.disarm(space_id)` |
| Arm Group | `SpaceSecurityService.armGroup(space_id, group_id)` |
| Code | Optional, user-configurable in config_flow |
| Hub online | `LiteSpace.hub_connection_status` as extra attribute |

If the hub has **group mode** active (`SecurityMode.GROUP`), an additional alarm_control_panel is created per group.

### Binary Sensors (1 per device with binary state)

| HA device class | Ajax device types | Proto field |
|---|---|---|
| `door` | DoorProtect, DoorProtectPlus, DoorProtectFibra... | status.open_close |
| `motion` | MotionProtect, MotionCam, CombiProtect... | status.motion |
| `smoke` | FireProtect, FireProtect2... | status.smoke_chamber |
| `moisture` | LeaksProtect | status.leak |
| `vibration` | DoorProtect (shock), GlassProtect | status.glass_break / shock |
| `tamper` | All devices | status.tamper |
| `connectivity` | All devices | device_state == OFFLINE |
| `battery` | All (with battery) | status.battery.is_low |
| `problem` | All devices | malfunctions > 0 |

### Sensors (diagnostic/numeric)

| Type | Proto field | Unit |
|---|---|---|
| Battery level | status.battery.percentage | % |
| Signal strength | status.signal_level | dBm / enum |
| Temperature | status.temperature | °C |
| Humidity | status.humidity | % |
| CO2 | status.co2 | ppm |
| Last event | last event from stream | timestamp |

### Switches (1 per channel)

| Ajax device types | Channels |
|---|---|
| Relay | 1 |
| WallSwitch | 1 |
| Socket | 1 |
| LightSwitch | 1 |
| LightSwitchTwoGang | 2 (CHANNEL_1, CHANNEL_2) |

Commands: `DeviceCommandDeviceOn/Off(hub_id, device_id, object_type, channels)`

### Lights (dimmers)

| Ajax device types | Capability |
|---|---|
| LightSwitchDimmer | brightness (0-100%) |

Command: `DeviceCommandBrightness(hub_id, device_id, object_type, brightness, channels, ABSOLUTE)`

---

## Data Update Strategy

The `coordinator.py` uses a hybrid model:

1. **Initial load**: `FindUserSpacesWithPagination` + `StreamLightDevices` snapshot
2. **Real-time**: `StreamLightDevices` server-stream (gRPC) — receives incremental updates without polling
3. **Fallback**: If the stream drops, reconnect with backoff. Meanwhile, poll every 30s via snapshot
4. **Security state**: Updated with each stream message (includes arm/disarm changes)

---

## Config Flow

```
Step 1: Credentials
  ├── email (str)
  ├── password (str, input type password)
  └── [Submit]
      ├── Success → Step 3
      ├── 2FA required → Step 2
      ├── Invalid credentials → error on Step 1
      └── Account locked → abort

Step 2: 2FA Code (TOTP)
  ├── totp_code (str, 6 digits)
  └── [Submit]
      ├── Success → Step 3
      └── Invalid TOTP → error, retry

Step 3: Space/Hub Selection
  ├── List of available spaces (multiselect if multiple)
  └── [Submit] → Creates config_entry, starts coordinator
```

Options flow (post-setup):
- Fallback polling interval (30-300s, default 30s)
- Enable/disable PIN code for arm/disarm
- Enable/disable specific entity types

---

## Error Handling and Graceful Degradation

### Error Mapping

| gRPC Error | Action |
|---|---|
| `UNAVAILABLE` | Retry with backoff (3 attempts) |
| `UNAUTHENTICATED` | Auto re-login; if fails → `ConfigEntryNotReady` |
| `PERMISSION_DENIED` | Log warning, mark entity as unavailable |
| `DEADLINE_EXCEEDED` | Retry with backoff |
| `NOT_FOUND` (device/space) | Remove entity from registry |
| Stream dropped | Reconnect with exponential backoff (1s→2s→4s→8s→max 60s) |
| Hub offline | All hub entities → `unavailable` |

### Degradation Behavior

- **Hub offline**: Entities report `unavailable`, coordinator keeps trying to reconnect
- **Stream dropped**: Fallback to polling, entities keep their last known state
- **Login failed on restart**: `ConfigEntryNotReady` → HA auto-retries with backoff
- **2FA activated post-setup**: Detected on refresh, raises `ConfigEntryAuthFailed` → user re-configures via reauth flow
- **Device disappears from hub**: Removed from HA device registry on next snapshot

### State Persistence

Persisted in `config_entry.data`:
- `session_token` (hex)
- `device_id` (UUID of the emulated "device")
- `user_hex_id`

Persisted in `hass.data`:
- Last full device snapshot (for fast startup after restart)

---

## Testing Strategy

### Unit Tests (`tests/unit/`)

- `test_session.py` — login, refresh, 2FA, error handling. Mocked gRPC channel
- `test_spaces.py` — list spaces, parse security state
- `test_security.py` — arm, disarm, night mode, group arming
- `test_devices.py` — parse snapshots, parse incremental updates, model mapping
- `test_commands.py` — on/off/bypass/brightness with all channel types
- `test_coordinator.py` — lifecycle, fallback polling, reconnect
- `test_config_flow.py` — full flow including 2FA and reauth
- `test_entities.py` — correct state mapping for each entity type

Coverage target: >80%.

### E2E Tests (`tests/e2e/`)

- `test_real_connection.py` — real login, list spaces, get devices
- `test_real_arming.py` — arm/disarm (marked `@pytest.mark.destructive`, skipped by default)

Require `AJAX_EMAIL` + `AJAX_PASSWORD` env vars. Run in Docker.

### Interactive Test Script (`scripts/test_connection.py`)

- Connects with real credentials via env vars
- Displays spaces, devices, states
- Allows interactive arm/disarm
- Runs in Docker: `make cli`

---

## Development Environment

### Docker (Dockerfile.dev)

Base image `python:3.12-slim` with multi-version support (`ARG PYTHON_VERSION`). Includes:
- `grpcio-tools` (proto compilation)
- `pytest`, `pytest-cov`, `pytest-asyncio`
- `ruff` (lint + format), `mypy` (type checking)
- `vulture` (dead code detection)
- `homeassistant` as test dependency

### Makefile Targets

| Target | Description |
|---|---|
| `make check` | lint + format-check + typecheck + tests + vulture |
| `make test` | `pytest tests/unit/ --cov --cov-fail-under=80` |
| `make test-e2e` | `pytest tests/e2e/` (requires env vars) |
| `make lint` | `ruff check .` |
| `make format` | `ruff format .` |
| `make typecheck` | `mypy custom_components/ajax_cobranded/` |
| `make dead-code` | `vulture custom_components/ajax_cobranded/` |
| `make proto` | `scripts/compile_protos.sh` — compiles proto_src/ → proto/ |
| `make cli` | Interactive script to test connection against real system |
| `make build` | Validates everything passes before release |

### CI (GitHub Actions)

```yaml
matrix:
  python-version: ["3.12", "3.13"]

steps:
  - docker build --build-arg PYTHON_VERSION=${{ matrix.python-version }}
  - make check  # Exactly the same as local
```

### Pre-push Hook

```bash
#!/bin/sh
make check || exit 1
```

Installed via `.pre-commit-config.yaml`.

---

## Versioning and Commits

- Strict semantic versioning in `pyproject.toml`
- Conventional commits: `feat(alarm):`, `fix(api):`, `docs:`, `chore:`, `refactor:`, `test:`
- 1-2 commits per logical change
- No auto-commit — always explicit confirmation

---

## Documentation

### README.md

- What it is, requirements, installation (HACS + manual)
- Step-by-step configuration with config flow
- Entity table with examples
- Compatible Ajax device table
- Automation and Lovelace card examples
- Troubleshooting
- Roadmap of pending features

### CHANGELOG.md

Keep a Changelog format. Starting with `0.1.0`.

### CONTRIBUTING.md

- Dev setup: `git clone` + `make proto` + `make check`
- Everything in Docker, zero local dependencies
- Commit conventions
- How to add support for a new device type
- How to run E2E tests against real system

### Translations

| File | Language | Coverage |
|---|---|---|
| `strings.json` | English | 100% (base) |
| `translations/es.json` | Spanish | 100% |
| `translations/ca.json` | Catalan | 100% |

### HACS Distribution

- `hacs.json` with metadata
- `manifest.json` with `"version"`, `"integration_type": "hub"`, dependencies (`grpcio`, `protobuf`)
- Validation with `hassfest` integrated in `make check`

### Reverse Engineering Document (LOCAL ONLY)

`docs/reverse-engineering/ajax-grpc-api.md` — full documentation of the gRPC API surface extracted from APK decompilation. Added to `.gitignore` to prevent publication.

---

## Key gRPC Services Reference

### Authentication (v3 mobilegwsvc)

| Service | Method | Purpose |
|---|---|---|
| `LoginByPasswordService` | `execute` | Login with email + SHA-256 password |
| `LoginByTotpService` | `execute` | 2FA login with TOTP code |
| `LoginByAuthTokenService` | `execute` | Session refresh with existing token |
| `LogoutService` | `execute` | Logout |

### Security (v2 mobile)

| Service | Method | Purpose |
|---|---|---|
| `SpaceSecurityService` | `arm` | Arm space (full) |
| `SpaceSecurityService` | `disarm` | Disarm space |
| `SpaceSecurityService` | `armToNightMode` | Arm night mode |
| `SpaceSecurityService` | `disarmFromNightMode` | Disarm from night mode |
| `SpaceSecurityService` | `setSecurityMode` | Set REGULAR/GROUP mode |
| `SpaceSecurityService` | `armGroup` | Arm specific group |
| `SpaceSecurityService` | `disarmGroup` | Disarm specific group |

### Spaces and Devices (v3 mobilegwsvc)

| Service | Method | Purpose |
|---|---|---|
| `FindUserSpacesWithPaginationService` | `execute` | List user's spaces/hubs |
| `StreamLightDevicesService` | `execute` | Server-stream of all devices (snapshot + updates) |
| `StreamHubDeviceService` | `execute` | Server-stream of single device details |
| `UpdateHubDeviceService` | `execute` | Update device settings |

### Device Commands (v3 mobilegwsvc)

| Service | Method | Purpose |
|---|---|---|
| `DeviceCommandDeviceOnService` | `execute` | Turn on relay/switch |
| `DeviceCommandDeviceOffService` | `execute` | Turn off relay/switch |
| `DeviceCommandDeviceBypassService` | `execute` | Bypass device |
| `DeviceCommandBrightnessService` | `execute` | Set dimmer brightness |

### gRPC Metadata Headers

**Session interceptor:**
- `client-session-token`: hex(session_token)
- `a911-user-id`: user_hex_id

**Device info interceptor:**
- `client-os`: `"Android"`
- `client-version-major`: `"3.30"`
- `application-label`: `"Protegim"`
- `client-device-type`: `"MOBILE"`
- `client-device-id`: persisted UUID
- `client-app-type`: `"USER"`
