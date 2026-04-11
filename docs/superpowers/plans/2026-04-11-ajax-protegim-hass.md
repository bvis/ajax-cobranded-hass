# Ajax Security Home Assistant Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Home Assistant custom integration that communicates with Ajax Security Systems via gRPC (same protocol as the mobile app), supporting alarm control, binary sensors, numeric sensors, switches, and lights.

**Architecture:** A pure Python gRPC client (`api/`) talks to `mobile-gw.prod.ajax.systems:443` using protobuf. A `DataUpdateCoordinator` bridges the API to HA entities. The gRPC client has zero HA dependencies and can be used standalone.

**Tech Stack:** Python 3.12+, grpcio, grpcio-tools, protobuf, Home Assistant Core, pytest, ruff, mypy

---

## File Map

### Infrastructure (Tasks 1-2)
| File | Responsibility |
|---|---|
| `Dockerfile.dev` | Dev container with all tools |
| `Makefile` | Build/test/lint targets |
| `pyproject.toml` | Project metadata, dependencies, tool config |
| `.pre-commit-config.yaml` | Pre-push hook config |
| `.gitignore` | Ignore patterns |
| `scripts/compile_protos.sh` | Compiles proto_src/ → custom_components/ajax_cobranded/proto/ |

### Proto Sources (Task 3)
| Directory | Responsibility |
|---|---|
| `proto_src/` | Raw .proto files extracted from APK decompilation |
| `custom_components/ajax_cobranded/proto/` | Auto-generated Python stubs |

### API Client (Tasks 4-8)
| File | Responsibility |
|---|---|
| `custom_components/ajax_cobranded/api/__init__.py` | Public API exports |
| `custom_components/ajax_cobranded/api/models.py` | Python dataclasses: Space, Device, DeviceStatus |
| `custom_components/ajax_cobranded/api/session.py` | Login, 2FA, token refresh, gRPC interceptors |
| `custom_components/ajax_cobranded/api/client.py` | AjaxGrpcClient: channel setup, high-level methods |
| `custom_components/ajax_cobranded/api/spaces.py` | List spaces, parse security state |
| `custom_components/ajax_cobranded/api/security.py` | Arm, disarm, night mode, group operations |
| `custom_components/ajax_cobranded/api/devices.py` | Stream devices, parse snapshots/updates, send commands |

### HA Integration (Tasks 9-14)
| File | Responsibility |
|---|---|
| `custom_components/ajax_cobranded/__init__.py` | Integration setup/teardown |
| `custom_components/ajax_cobranded/manifest.json` | HA integration metadata |
| `custom_components/ajax_cobranded/const.py` | Domain, platforms, defaults |
| `custom_components/ajax_cobranded/config_flow.py` | Config + options flow with 2FA support |
| `custom_components/ajax_cobranded/coordinator.py` | DataUpdateCoordinator with stream + fallback |
| `custom_components/ajax_cobranded/alarm_control_panel.py` | Alarm panel entity |
| `custom_components/ajax_cobranded/binary_sensor.py` | Binary sensor entities |
| `custom_components/ajax_cobranded/sensor.py` | Diagnostic/numeric sensor entities |
| `custom_components/ajax_cobranded/switch.py` | Relay/switch entities |
| `custom_components/ajax_cobranded/light.py` | Dimmer entities |
| `custom_components/ajax_cobranded/strings.json` | EN translations |
| `custom_components/ajax_cobranded/translations/es.json` | ES translations |
| `custom_components/ajax_cobranded/translations/ca.json` | CA translations |

### Tests (throughout)
| File | Responsibility |
|---|---|
| `tests/conftest.py` | Shared fixtures |
| `tests/unit/test_models.py` | Model dataclass tests |
| `tests/unit/test_session.py` | Session/auth tests |
| `tests/unit/test_spaces.py` | Spaces parsing tests |
| `tests/unit/test_security.py` | Arm/disarm tests |
| `tests/unit/test_devices.py` | Device streaming/command tests |
| `tests/unit/test_config_flow.py` | Config flow tests |
| `tests/unit/test_coordinator.py` | Coordinator lifecycle tests |
| `tests/unit/test_alarm_control_panel.py` | Alarm entity tests |
| `tests/unit/test_binary_sensor.py` | Binary sensor entity tests |
| `tests/unit/test_sensor.py` | Sensor entity tests |
| `tests/unit/test_switch.py` | Switch entity tests |
| `tests/unit/test_light.py` | Light entity tests |
| `tests/e2e/test_real_connection.py` | E2E against real Ajax API |

### Documentation (Task 15)
| File | Responsibility |
|---|---|
| `README.md` | User-facing docs |
| `CHANGELOG.md` | Release history |
| `CONTRIBUTING.md` | Dev guide |
| `hacs.json` | HACS metadata |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.pre-commit-config.yaml`
- Create: `Dockerfile.dev`
- Create: `Makefile`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "ajax-cobranded-hass"
version = "0.1.0"
description = "Home Assistant integration for Ajax Security Systems (Protegim) via gRPC"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "grpcio>=1.60.0",
    "protobuf>=4.25.0",
]

[project.optional-dependencies]
dev = [
    "grpcio-tools>=1.60.0",
    "homeassistant>=2024.1.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.4.0",
    "mypy>=1.8.0",
    "mypy-protobuf>=3.5.0",
    "vulture>=2.11",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "e2e: end-to-end tests against real Ajax API",
    "destructive: tests that modify system state (arm/disarm)",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "ANN", "B", "A", "SIM", "TCH"]
ignore = ["ANN101", "ANN102"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.vulture]
paths = ["custom_components/ajax_cobranded"]
min_confidence = 80
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg

# Virtual environments
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp

# Testing
.coverage
htmlcov/
.pytest_cache/

# mypy
.mypy_cache/

# ruff
.ruff_cache/

# Generated proto files
custom_components/ajax_cobranded/proto/*_pb2.py
custom_components/ajax_cobranded/proto/*_pb2_grpc.py
custom_components/ajax_cobranded/proto/*_pb2.pyi

# Reverse engineering docs (local only)
docs/reverse-engineering/

# Environment
.env
.env.*
```

- [ ] **Step 3: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: local
    hooks:
      - id: check
        name: Full check (lint + typecheck + test)
        entry: make check
        language: system
        pass_filenames: false
        stages: [pre-push]
```

- [ ] **Step 4: Create Dockerfile.dev**

```dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

CMD ["make", "check"]
```

- [ ] **Step 5: Create Makefile**

```makefile
.PHONY: check test test-e2e lint format typecheck dead-code proto cli build

DOCKER_IMAGE = ajax-protegim-dev
DOCKER_RUN = docker run --rm -v $(PWD):/app -w /app $(DOCKER_IMAGE)

build-docker:
	docker build -f Dockerfile.dev -t $(DOCKER_IMAGE) .

check: lint format-check typecheck test dead-code
	@echo "All checks passed."

test:
	pytest tests/unit/ -v --cov=custom_components/ajax_cobranded --cov-fail-under=80 --cov-report=term-missing

test-e2e:
	pytest tests/e2e/ -v -m "e2e and not destructive"

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

typecheck:
	mypy custom_components/ajax_cobranded/

dead-code:
	vulture custom_components/ajax_cobranded/

proto:
	bash scripts/compile_protos.sh

cli:
	python scripts/test_connection.py
```

- [ ] **Step 6: Create directory structure**

```bash
mkdir -p custom_components/ajax_cobranded/api
mkdir -p custom_components/ajax_cobranded/proto
mkdir -p custom_components/ajax_cobranded/translations
mkdir -p tests/unit tests/e2e
mkdir -p scripts
mkdir -p proto_src
touch custom_components/__init__.py
touch custom_components/ajax_cobranded/__init__.py
touch custom_components/ajax_cobranded/api/__init__.py
touch custom_components/ajax_cobranded/proto/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/e2e/__init__.py
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore .pre-commit-config.yaml Dockerfile.dev Makefile \
    custom_components/ tests/ scripts/ proto_src/
git commit -m "chore: scaffold project structure with Docker dev environment"
```

---

## Task 2: Proto Compilation Pipeline

**Files:**
- Create: `scripts/compile_protos.sh`
- Create: `custom_components/ajax_cobranded/proto/__init__.py` (with re-exports)

- [ ] **Step 1: Create compile_protos.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROTO_SRC="$PROJECT_ROOT/proto_src"
PROTO_OUT="$PROJECT_ROOT/custom_components/ajax_cobranded/proto"

if [ ! -d "$PROTO_SRC" ]; then
    echo "Error: proto_src/ directory not found at $PROTO_SRC"
    exit 1
fi

echo "Cleaning old generated files..."
find "$PROTO_OUT" -name '*_pb2.py' -o -name '*_pb2_grpc.py' -o -name '*_pb2.pyi' | xargs rm -f

echo "Compiling proto files..."
python -m grpc_tools.protoc \
    --proto_path="$PROTO_SRC" \
    --python_out="$PROTO_OUT" \
    --grpc_python_out="$PROTO_OUT" \
    --mypy_out="$PROTO_OUT" \
    $(find "$PROTO_SRC" -name '*.proto')

# Fix imports in generated files: replace absolute proto paths with relative
echo "Fixing imports in generated files..."
find "$PROTO_OUT" -name '*_pb2*.py' -exec sed -i.bak \
    's/^from systems\./from .systems_/g; s/^from v3\./from .v3_/g; s/^from v1\./from .v1_/g' {} \;
find "$PROTO_OUT" -name '*.bak' -delete

echo "Proto compilation complete. Output: $PROTO_OUT"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/compile_protos.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/compile_protos.sh
git commit -m "chore: add proto compilation script"
```

---

## Task 3: Extract and Organize Proto Sources

**Files:**
- Create: `proto_src/` tree with .proto files from decompiled APK

The proto files needed are in `/tmp/protegim-decompiled/resources/`. We need a curated subset — only the protos required for our integration. This task copies and organizes them.

- [ ] **Step 1: Copy the required proto files from the decompiled APK**

Copy these directories from `/tmp/protegim-decompiled/resources/` into `proto_src/`:

```bash
# Auth protos (v3)
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/login_by_password proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/login_by_auth_token proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/login_by_totp proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/logout proto_src/v3/mobilegwsvc/service/

# Space listing (v3)
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/find_user_spaces_with_pagination proto_src/v3/mobilegwsvc/service/

# Device streaming (v3)
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/stream_light_devices proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/stream_hub_device proto_src/v3/mobilegwsvc/service/

# Device commands (v3)
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/device_command_device_on proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/device_command_device_off proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/device_command_device_bypass proto_src/v3/mobilegwsvc/service/
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/service/device_command_brightness proto_src/v3/mobilegwsvc/service/

# Security (v2)
cp -r /tmp/protegim-decompiled/resources/systems/ajax/api/mobile/v2/space/security proto_src/systems/ajax/api/mobile/v2/space/

# Common models — copy ALL transitive dependencies
cp -r /tmp/protegim-decompiled/resources/v3/mobilegwsvc/commonmodels proto_src/v3/mobilegwsvc/
cp -r /tmp/protegim-decompiled/resources/systems proto_src/
```

- [ ] **Step 2: Verify proto compilation succeeds**

Run: `bash scripts/compile_protos.sh`
Expected: Compiles without errors. Generated `*_pb2.py` files in `custom_components/ajax_cobranded/proto/`.

Note: If there are import resolution errors, iteratively add missing proto dependencies from `/tmp/protegim-decompiled/resources/` until compilation succeeds. The proto files have deep transitive dependencies — it may be simpler to copy the entire `resources/` tree and let the compiler resolve everything.

- [ ] **Step 3: Verify generated files exist**

```bash
ls custom_components/ajax_cobranded/proto/*_pb2.py | head -20
```

Expected: Multiple `*_pb2.py` files present.

- [ ] **Step 4: Commit**

```bash
git add proto_src/ custom_components/ajax_cobranded/proto/__init__.py
git commit -m "chore: add proto source files and compile pipeline"
```

Note: The generated `*_pb2.py` files are in `.gitignore`. Only `proto_src/` is committed. Users run `make proto` to compile.

---

## Task 4: Data Models

**Files:**
- Create: `custom_components/ajax_cobranded/api/models.py`
- Create: `tests/unit/test_models.py`
- Create: `custom_components/ajax_cobranded/const.py`

- [ ] **Step 1: Create const.py**

```python
"""Constants for the Ajax Security integration."""

from enum import IntEnum, StrEnum

DOMAIN = "ajax_cobranded"

GRPC_HOST = "mobile-gw.prod.ajax.systems"
GRPC_PORT = 443

CLIENT_OS = "Android"
CLIENT_VERSION = "3.30"
APPLICATION_LABEL = "Protegim"
CLIENT_DEVICE_TYPE = "MOBILE"
CLIENT_APP_TYPE = "USER"

SESSION_REFRESH_INTERVAL = 780  # 13 minutes in seconds
STREAM_RECONNECT_MAX_BACKOFF = 60  # seconds
DEFAULT_POLL_INTERVAL = 30  # seconds fallback
GRPC_TIMEOUT = 10.0  # seconds
GRPC_STREAM_TIMEOUT = 30.0  # seconds
MAX_RETRIES = 3
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60  # seconds


class SecurityState(IntEnum):
    """Maps DisplayedSpaceSecurityState proto enum."""

    NONE = 0
    ARMED = 1
    DISARMED = 2
    NIGHT_MODE = 3
    PARTIALLY_ARMED = 4
    AWAITING_EXIT_TIMER = 5
    AWAITING_SECOND_STAGE = 6
    TWO_STAGE_INCOMPLETE = 7
    AWAITING_VDS = 8


class ConnectionStatus(IntEnum):
    """Maps mobile v2 ConnectionStatus proto enum."""

    UNSPECIFIED = 0
    ONLINE = 1
    OFFLINE = 2


class UserRole(IntEnum):
    """Maps UserRole proto enum."""

    UNSPECIFIED = 0
    USER = 1
    PRO = 2


class DeviceState(StrEnum):
    """Simplified device states from LightDeviceState."""

    ONLINE = "online"
    OFFLINE = "offline"
    LOCKED = "locked"
    SUSPENDED = "suspended"
    UPDATING = "updating"
    BATTERY_SAVING = "battery_saving"
    WALK_TEST = "walk_test"
    ADDING = "adding"
    NOT_MIGRATED = "not_migrated"
    UNKNOWN = "unknown"
```

- [ ] **Step 2: Write failing tests for models**

```python
"""Tests for API data models."""

from custom_components.ajax_cobranded.api.models import (
    BatteryInfo,
    Device,
    DeviceCommand,
    Space,
)
from custom_components.ajax_cobranded.const import (
    ConnectionStatus,
    DeviceState,
    SecurityState,
)


class TestSpace:
    def test_creation(self) -> None:
        space = Space(
            id="space-1",
            hub_id="hub-1",
            name="Home",
            security_state=SecurityState.DISARMED,
            connection_status=ConnectionStatus.ONLINE,
            malfunctions_count=0,
        )
        assert space.id == "space-1"
        assert space.hub_id == "hub-1"
        assert space.name == "Home"
        assert space.security_state == SecurityState.DISARMED
        assert space.connection_status == ConnectionStatus.ONLINE
        assert space.is_online is True

    def test_is_online_false_when_offline(self) -> None:
        space = Space(
            id="s1",
            hub_id="h1",
            name="Office",
            security_state=SecurityState.ARMED,
            connection_status=ConnectionStatus.OFFLINE,
            malfunctions_count=0,
        )
        assert space.is_online is False

    def test_is_armed(self) -> None:
        for state in (SecurityState.ARMED, SecurityState.NIGHT_MODE, SecurityState.PARTIALLY_ARMED):
            space = Space(
                id="s",
                hub_id="h",
                name="X",
                security_state=state,
                connection_status=ConnectionStatus.ONLINE,
                malfunctions_count=0,
            )
            assert space.is_armed is True

    def test_is_not_armed(self) -> None:
        space = Space(
            id="s",
            hub_id="h",
            name="X",
            security_state=SecurityState.DISARMED,
            connection_status=ConnectionStatus.ONLINE,
            malfunctions_count=0,
        )
        assert space.is_armed is False


class TestDevice:
    def test_creation(self) -> None:
        device = Device(
            id="dev-1",
            hub_id="hub-1",
            name="Front Door",
            device_type="DoorProtect",
            room_id="room-1",
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={},
            battery=BatteryInfo(level=95, is_low=False),
        )
        assert device.id == "dev-1"
        assert device.name == "Front Door"
        assert device.device_type == "DoorProtect"
        assert device.is_online is True
        assert device.battery is not None
        assert device.battery.level == 95

    def test_is_online_false(self) -> None:
        device = Device(
            id="d",
            hub_id="h",
            name="X",
            device_type="MotionProtect",
            room_id=None,
            group_id=None,
            state=DeviceState.OFFLINE,
            malfunctions=0,
            bypassed=False,
            statuses={},
            battery=None,
        )
        assert device.is_online is False


class TestDeviceCommand:
    def test_on_command(self) -> None:
        cmd = DeviceCommand.on(hub_id="h1", device_id="d1", device_type="Relay", channels=[1])
        assert cmd.action == "on"
        assert cmd.hub_id == "h1"
        assert cmd.channels == [1]

    def test_off_command(self) -> None:
        cmd = DeviceCommand.off(hub_id="h1", device_id="d1", device_type="Socket")
        assert cmd.action == "off"
        assert cmd.channels == []

    def test_brightness_command(self) -> None:
        cmd = DeviceCommand.brightness(
            hub_id="h1",
            device_id="d1",
            device_type="LightSwitchDimmer",
            brightness=75,
            channels=[1],
        )
        assert cmd.action == "brightness"
        assert cmd.brightness == 75
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_models.py -v`
Expected: FAIL — `models` module not found.

- [ ] **Step 4: Implement models.py**

```python
"""Data models for the Ajax gRPC API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from custom_components.ajax_cobranded.const import (
    ConnectionStatus,
    DeviceState,
    SecurityState,
)


@dataclass(frozen=True)
class Space:
    """Represents an Ajax space (hub)."""

    id: str
    hub_id: str
    name: str
    security_state: SecurityState
    connection_status: ConnectionStatus
    malfunctions_count: int

    @property
    def is_online(self) -> bool:
        return self.connection_status == ConnectionStatus.ONLINE

    @property
    def is_armed(self) -> bool:
        return self.security_state in (
            SecurityState.ARMED,
            SecurityState.NIGHT_MODE,
            SecurityState.PARTIALLY_ARMED,
        )


@dataclass(frozen=True)
class BatteryInfo:
    """Battery status for a device."""

    level: int  # 0-100 percentage
    is_low: bool


@dataclass(frozen=True)
class Device:
    """Represents an Ajax device."""

    id: str
    hub_id: str
    name: str
    device_type: str
    room_id: str | None
    group_id: str | None
    state: DeviceState
    malfunctions: int
    bypassed: bool
    statuses: dict[str, Any]
    battery: BatteryInfo | None

    @property
    def is_online(self) -> bool:
        return self.state == DeviceState.ONLINE


@dataclass(frozen=True)
class DeviceCommand:
    """Represents a command to send to a device."""

    action: str
    hub_id: str
    device_id: str
    device_type: str
    channels: list[int] = field(default_factory=list)
    brightness: int | None = None

    @classmethod
    def on(
        cls,
        hub_id: str,
        device_id: str,
        device_type: str,
        channels: list[int] | None = None,
    ) -> DeviceCommand:
        return cls(
            action="on",
            hub_id=hub_id,
            device_id=device_id,
            device_type=device_type,
            channels=channels or [],
        )

    @classmethod
    def off(
        cls,
        hub_id: str,
        device_id: str,
        device_type: str,
        channels: list[int] | None = None,
    ) -> DeviceCommand:
        return cls(
            action="off",
            hub_id=hub_id,
            device_id=device_id,
            device_type=device_type,
            channels=channels or [],
        )

    @classmethod
    def brightness(
        cls,
        hub_id: str,
        device_id: str,
        device_type: str,
        brightness: int,
        channels: list[int] | None = None,
    ) -> DeviceCommand:
        return cls(
            action="brightness",
            hub_id=hub_id,
            device_id=device_id,
            device_type=device_type,
            channels=channels or [],
            brightness=brightness,
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_models.py -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/ajax_cobranded/const.py \
    custom_components/ajax_cobranded/api/models.py \
    tests/unit/test_models.py
git commit -m "feat(api): add data models and constants"
```

---

## Task 5: gRPC Session Management

**Files:**
- Create: `custom_components/ajax_cobranded/api/session.py`
- Create: `tests/unit/test_session.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create conftest.py with shared fixtures**

```python
"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

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
```

- [ ] **Step 2: Write failing tests for session**

```python
"""Tests for gRPC session management."""

from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.session import AjaxSession, AuthenticationError


class TestPasswordHashing:
    def test_hash_password(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        result = session._hash_password("mypassword")
        expected = hashlib.sha256(b"mypassword").hexdigest()
        assert result == expected

    def test_hash_password_empty(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        result = session._hash_password("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected


class TestTokenConversion:
    def test_bytes_to_hex(self) -> None:
        token_bytes = bytes.fromhex("aabbccdd")
        result = AjaxSession._token_to_hex(token_bytes)
        assert result == "aabbccdd"

    def test_hex_to_bytes(self) -> None:
        result = AjaxSession._token_from_hex("aabbccdd")
        assert result == bytes.fromhex("aabbccdd")


class TestSessionMetadata:
    def test_session_metadata_keys(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "aabbccdd"
        session._user_hex_id = "user123"
        session._device_id = "device-uuid-1"

        meta = session.get_session_metadata()
        keys = {k for k, v in meta}
        assert "client-session-token" in keys
        assert "a911-user-id" in keys

    def test_device_info_metadata_keys(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._device_id = "device-uuid-1"

        meta = session.get_device_info_metadata()
        meta_dict = dict(meta)
        assert meta_dict["client-os"] == "Android"
        assert meta_dict["client-version-major"] == "3.30"
        assert meta_dict["application-label"] == "Protegim"
        assert meta_dict["client-device-type"] == "MOBILE"
        assert meta_dict["client-app-type"] == "USER"
        assert meta_dict["client-device-id"] == "device-uuid-1"

    def test_combined_metadata(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "aabb"
        session._user_hex_id = "user1"
        session._device_id = "dev1"

        meta = session.get_call_metadata()
        meta_dict = dict(meta)
        # Should have both session and device info keys
        assert "client-session-token" in meta_dict
        assert "client-os" in meta_dict


class TestAuthState:
    def test_is_authenticated_false_initially(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = None
        session._user_hex_id = None
        assert session.is_authenticated is False

    def test_is_authenticated_true(self) -> None:
        session = AjaxSession.__new__(AjaxSession)
        session._session_token = "token"
        session._user_hex_id = "user"
        assert session.is_authenticated is True
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_session.py -v`
Expected: FAIL — `session` module not found.

- [ ] **Step 4: Implement session.py**

```python
"""gRPC session management for Ajax Systems API."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from custom_components.ajax_cobranded.const import (
    APPLICATION_LABEL,
    CLIENT_APP_TYPE,
    CLIENT_DEVICE_TYPE,
    CLIENT_OS,
    CLIENT_VERSION,
    UserRole,
)


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class TwoFactorRequired(Exception):
    """Raised when 2FA is needed."""

    def __init__(self, request_id: str) -> None:
        super().__init__("Two-factor authentication required")
        self.request_id = request_id


class AjaxSession:
    """Manages authentication and session state for the Ajax gRPC API."""

    def __init__(self, device_id: str | None = None) -> None:
        self._session_token: str | None = None
        self._user_hex_id: str | None = None
        self._device_id: str = device_id or str(uuid.uuid4())
        self._email: str | None = None
        self._password_hash: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self._session_token is not None and self._user_hex_id is not None

    @property
    def session_token(self) -> str | None:
        return self._session_token

    @property
    def user_hex_id(self) -> str | None:
        return self._user_hex_id

    @property
    def device_id(self) -> str:
        return self._device_id

    def set_credentials(self, email: str, password: str) -> None:
        self._email = email
        self._password_hash = self._hash_password(password)

    def set_session(self, session_token: str, user_hex_id: str) -> None:
        self._session_token = session_token
        self._user_hex_id = user_hex_id

    def clear_session(self) -> None:
        self._session_token = None
        self._user_hex_id = None

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _token_to_hex(token_bytes: bytes) -> str:
        return token_bytes.hex()

    @staticmethod
    def _token_from_hex(token_hex: str) -> bytes:
        return bytes.fromhex(token_hex)

    def get_session_metadata(self) -> list[tuple[str, str]]:
        if not self._session_token or not self._user_hex_id:
            return []
        return [
            ("client-session-token", self._session_token),
            ("a911-user-id", self._user_hex_id),
        ]

    def get_device_info_metadata(self) -> list[tuple[str, str]]:
        return [
            ("client-os", CLIENT_OS),
            ("client-version-major", CLIENT_VERSION),
            ("application-label", APPLICATION_LABEL),
            ("client-device-type", CLIENT_DEVICE_TYPE),
            ("client-device-id", self._device_id),
            ("client-app-type", CLIENT_APP_TYPE),
        ]

    def get_call_metadata(self) -> list[tuple[str, str]]:
        return self.get_session_metadata() + self.get_device_info_metadata()

    def get_login_params(self) -> dict[str, Any]:
        if not self._email or not self._password_hash:
            raise AuthenticationError("Credentials not set. Call set_credentials() first.")
        return {
            "email": self._email,
            "password_sha256_hash": self._password_hash,
            "user_role": UserRole.USER,
        }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_session.py -v`
Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add custom_components/ajax_cobranded/api/session.py \
    tests/unit/test_session.py tests/conftest.py
git commit -m "feat(api): add session management with auth metadata"
```

---

## Task 6: gRPC Client Core

**Files:**
- Create: `custom_components/ajax_cobranded/api/client.py`
- Create: `tests/unit/test_client.py`

- [ ] **Step 1: Write failing tests for client**

```python
"""Tests for the gRPC client core."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.session import AjaxSession, AuthenticationError
from custom_components.ajax_cobranded.const import GRPC_HOST, GRPC_PORT


class TestClientInit:
    def test_default_host_port(self) -> None:
        client = AjaxGrpcClient.__new__(AjaxGrpcClient)
        client._host = GRPC_HOST
        client._port = GRPC_PORT
        assert client._host == "mobile-gw.prod.ajax.systems"
        assert client._port == 443

    def test_session_created(self) -> None:
        client = AjaxGrpcClient(email="test@example.com", password="secret")
        assert isinstance(client._session, AjaxSession)
        assert client._session._email == "test@example.com"


class TestClientRetry:
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self) -> None:
        client = AjaxGrpcClient.__new__(AjaxGrpcClient)
        client._session = AjaxSession()

        call_count = 0

        async def flaky_call() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("UNAVAILABLE")
            return "success"

        result = await client._retry(flaky_call, max_retries=3, base_delay=0.01)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        client = AjaxGrpcClient.__new__(AjaxGrpcClient)
        client._session = AjaxSession()

        async def always_fails() -> str:
            raise ConnectionError("UNAVAILABLE")

        with pytest.raises(ConnectionError):
            await client._retry(always_fails, max_retries=2, base_delay=0.01)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_client.py -v`
Expected: FAIL — `client` module not found.

- [ ] **Step 3: Implement client.py**

```python
"""Core gRPC client for Ajax Systems API."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import grpc

from custom_components.ajax_cobranded.api.session import (
    AjaxSession,
    AuthenticationError,
    TwoFactorRequired,
)
from custom_components.ajax_cobranded.const import (
    GRPC_HOST,
    GRPC_PORT,
    GRPC_TIMEOUT,
    MAX_RETRIES,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    SESSION_REFRESH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

# gRPC status codes that are transient and worth retrying
_TRANSIENT_CODES = {
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.DEADLINE_EXCEEDED,
    grpc.StatusCode.INTERNAL,
}


class AjaxGrpcClient:
    """High-level gRPC client for the Ajax mobile gateway."""

    def __init__(
        self,
        email: str,
        password: str,
        device_id: str | None = None,
        host: str = GRPC_HOST,
        port: int = GRPC_PORT,
    ) -> None:
        self._host = host
        self._port = port
        self._session = AjaxSession(device_id=device_id)
        self._session.set_credentials(email, password)
        self._channel: grpc.aio.Channel | None = None
        self._rate_limit_timestamps: list[float] = []
        self._refresh_task: asyncio.Task[None] | None = None

    @property
    def session(self) -> AjaxSession:
        return self._session

    @property
    def is_connected(self) -> bool:
        return self._channel is not None and self._session.is_authenticated

    async def connect(self) -> None:
        """Establish the gRPC channel."""
        target = f"{self._host}:{self._port}"
        credentials = grpc.ssl_channel_credentials()
        self._channel = grpc.aio.secure_channel(target, credentials)
        _LOGGER.debug("gRPC channel opened to %s", target)

    async def close(self) -> None:
        """Close the gRPC channel and stop refresh."""
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            self._refresh_task = None
        if self._channel:
            await self._channel.close()
            self._channel = None
        self._session.clear_session()
        _LOGGER.debug("gRPC channel closed")

    def _get_channel(self) -> grpc.aio.Channel:
        if self._channel is None:
            raise ConnectionError("gRPC channel not connected. Call connect() first.")
        return self._channel

    async def _check_rate_limit(self) -> None:
        """Enforce client-side rate limiting."""
        now = time.monotonic()
        self._rate_limit_timestamps = [
            t for t in self._rate_limit_timestamps if now - t < RATE_LIMIT_WINDOW
        ]
        if len(self._rate_limit_timestamps) >= RATE_LIMIT_REQUESTS:
            wait = RATE_LIMIT_WINDOW - (now - self._rate_limit_timestamps[0])
            _LOGGER.warning("Rate limit reached, waiting %.1fs", wait)
            await asyncio.sleep(wait)
        self._rate_limit_timestamps.append(time.monotonic())

    async def _retry(
        self,
        coro_fn: Callable[[], Awaitable[T]],
        max_retries: int = MAX_RETRIES,
        base_delay: float = 1.0,
    ) -> T:
        """Execute an async callable with retry and exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                return await coro_fn()
            except grpc.aio.AioRpcError as e:
                if e.code() not in _TRANSIENT_CODES:
                    raise
                last_error = e
            except (ConnectionError, OSError) as e:
                last_error = e

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt) * (0.8 + 0.4 * random.random())
                _LOGGER.debug(
                    "Retry %d/%d after %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    delay,
                    last_error,
                )
                await asyncio.sleep(delay)

        raise last_error  # type: ignore[misc]

    async def call_unary(
        self,
        method_path: str,
        request: Any,
        response_type: type[T],
        timeout: float = GRPC_TIMEOUT,
    ) -> T:
        """Make a unary gRPC call with metadata, rate limiting, and retry."""
        await self._check_rate_limit()
        channel = self._get_channel()
        metadata = self._session.get_call_metadata()

        async def _do_call() -> T:
            method = channel.unary_unary(
                method_path,
                request_serializer=request.SerializeToString,
                response_deserializer=response_type.FromString,
            )
            return await method(request, metadata=metadata, timeout=timeout)

        return await self._retry(_do_call)

    async def call_server_stream(
        self,
        method_path: str,
        request: Any,
        response_type: type[T],
        timeout: float | None = None,
    ) -> grpc.aio.UnaryStreamCall[Any, T]:
        """Open a server-streaming gRPC call."""
        await self._check_rate_limit()
        channel = self._get_channel()
        metadata = self._session.get_call_metadata()

        method = channel.unary_stream(
            method_path,
            request_serializer=request.SerializeToString,
            response_deserializer=response_type.FromString,
        )
        return method(request, metadata=metadata, timeout=timeout)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_client.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajax_cobranded/api/client.py tests/unit/test_client.py
git commit -m "feat(api): add gRPC client core with retry and rate limiting"
```

---

## Task 7: Spaces and Security API

**Files:**
- Create: `custom_components/ajax_cobranded/api/spaces.py`
- Create: `custom_components/ajax_cobranded/api/security.py`
- Create: `tests/unit/test_spaces.py`
- Create: `tests/unit/test_security.py`

This task depends on compiled protos. The implementation uses proto-generated stubs for request/response serialization. Since proto compilation may produce different import paths depending on the proto structure, the actual import paths will be determined after Task 3 is complete. The patterns below show the intended logic; adjust import paths to match the generated stubs.

- [ ] **Step 1: Write failing tests for spaces**

```python
"""Tests for spaces API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.api.models import Space
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import ConnectionStatus, SecurityState


class TestParseSpace:
    def test_parse_space_from_proto(self) -> None:
        """Test parsing a LiteSpace proto message into a Space model."""
        proto_space = MagicMock()
        proto_space.id = "space-abc"
        proto_space.hub_id = "hub-xyz"
        proto_space.profile.name = "My Home"
        proto_space.security_state = 2  # DISARMED
        proto_space.hub_connection_status = 1  # ONLINE
        proto_space.malfunctions_count = 0

        result = SpacesApi.parse_space(proto_space)

        assert isinstance(result, Space)
        assert result.id == "space-abc"
        assert result.hub_id == "hub-xyz"
        assert result.name == "My Home"
        assert result.security_state == SecurityState.DISARMED
        assert result.connection_status == ConnectionStatus.ONLINE

    def test_parse_space_armed(self) -> None:
        proto_space = MagicMock()
        proto_space.id = "s1"
        proto_space.hub_id = "h1"
        proto_space.profile.name = "Office"
        proto_space.security_state = 1  # ARMED
        proto_space.hub_connection_status = 1  # ONLINE
        proto_space.malfunctions_count = 2

        result = SpacesApi.parse_space(proto_space)
        assert result.security_state == SecurityState.ARMED
        assert result.malfunctions_count == 2

    def test_parse_space_hub_id_optional(self) -> None:
        """When hub_id is empty string, it should be stored as empty."""
        proto_space = MagicMock()
        proto_space.id = "s1"
        proto_space.hub_id = ""
        proto_space.profile.name = "Test"
        proto_space.security_state = 0
        proto_space.hub_connection_status = 0
        proto_space.malfunctions_count = 0

        result = SpacesApi.parse_space(proto_space)
        assert result.hub_id == ""
```

- [ ] **Step 2: Write failing tests for security**

```python
"""Tests for security API (arm/disarm)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.api.security import SecurityApi


class TestSecurityApiInit:
    def test_init(self) -> None:
        client = MagicMock()
        api = SecurityApi(client)
        assert api._client is client


class TestArmingCommands:
    def test_arm_builds_correct_request(self) -> None:
        """Verify arm() calls the correct gRPC method path."""
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        api._client.call_unary = AsyncMock()

        # We verify the method is callable and accepts space_id
        assert callable(api.arm)

    def test_disarm_builds_correct_request(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        api._client.call_unary = AsyncMock()
        assert callable(api.disarm)

    def test_arm_night_mode_builds_correct_request(self) -> None:
        api = SecurityApi.__new__(SecurityApi)
        api._client = MagicMock()
        api._client.call_unary = AsyncMock()
        assert callable(api.arm_night_mode)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_spaces.py tests/unit/test_security.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 4: Implement spaces.py**

```python
"""Spaces (hubs) API operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from custom_components.ajax_cobranded.api.models import Space
from custom_components.ajax_cobranded.const import ConnectionStatus, SecurityState

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

# gRPC method paths
_FIND_SPACES_METHOD = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".find_user_spaces_with_pagination.FindUserSpacesWithPaginationService/execute"
)


class SpacesApi:
    """API operations for spaces (hubs)."""

    def __init__(self, client: AjaxGrpcClient) -> None:
        self._client = client

    @staticmethod
    def parse_space(proto_space: Any) -> Space:
        """Parse a LiteSpace proto message into a Space model."""
        return Space(
            id=proto_space.id,
            hub_id=proto_space.hub_id if proto_space.hub_id else "",
            name=proto_space.profile.name,
            security_state=SecurityState(proto_space.security_state),
            connection_status=ConnectionStatus(proto_space.hub_connection_status),
            malfunctions_count=proto_space.malfunctions_count,
        )

    async def list_spaces(self) -> list[Space]:
        """Fetch all spaces for the authenticated user."""
        # Import generated proto stubs
        from custom_components.ajax_cobranded.proto import (
            find_user_spaces_with_pagination_pb2 as req_pb,
        )
        from custom_components.ajax_cobranded.proto import (
            find_user_spaces_with_pagination_pb2 as resp_pb,
        )

        request = req_pb.FindUserSpacesWithPaginationRequest(limit=100)
        response = await self._client.call_unary(
            _FIND_SPACES_METHOD,
            request,
            resp_pb.FindUserSpacesWithPaginationResponse,
        )

        if response.HasField("failure"):
            _LOGGER.error("Failed to list spaces: %s", response.failure)
            return []

        return [self.parse_space(s) for s in response.success.spaces]
```

- [ ] **Step 5: Implement security.py**

```python
"""Security API operations (arm/disarm)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

# gRPC method paths for SpaceSecurityService
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

    def _make_space_locator(self, space_id: str) -> Any:
        """Create a SpaceLocator proto with space_id."""
        from custom_components.ajax_cobranded.proto import space_locator_pb2

        return space_locator_pb2.SpaceLocator(space_id=space_id)

    async def arm(self, space_id: str, ignore_alarms: bool = False) -> None:
        """Arm a space."""
        from custom_components.ajax_cobranded.proto import arm_request_pb2 as pb

        request = pb.ArmSpaceRequest(
            space_locator=self._make_space_locator(space_id),
            ignore_alarms=ignore_alarms,
        )
        response = await self._client.call_unary(
            _ARM_METHOD, request, pb.ArmSpaceResponse
        )
        if response.HasField("failure"):
            raise SecurityError(f"Arm failed: {response.failure}")

    async def disarm(self, space_id: str) -> None:
        """Disarm a space."""
        from custom_components.ajax_cobranded.proto import disarm_request_pb2 as pb

        request = pb.DisarmSpaceRequest(
            space_locator=self._make_space_locator(space_id),
        )
        response = await self._client.call_unary(
            _DISARM_METHOD, request, pb.DisarmSpaceResponse
        )
        if response.HasField("failure"):
            raise SecurityError(f"Disarm failed: {response.failure}")

    async def arm_night_mode(self, space_id: str, ignore_alarms: bool = False) -> None:
        """Arm a space in night mode."""
        from custom_components.ajax_cobranded.proto import arm_to_night_mode_request_pb2 as pb

        request = pb.ArmSpaceToNightModeRequest(
            space_locator=self._make_space_locator(space_id),
            ignore_alarms=ignore_alarms,
        )
        response = await self._client.call_unary(
            _ARM_NIGHT_METHOD, request, pb.ArmSpaceToNightModeResponse
        )
        if response.HasField("failure"):
            raise SecurityError(f"Arm night mode failed: {response.failure}")

    async def arm_group(
        self, space_id: str, group_id: str, ignore_alarms: bool = False
    ) -> None:
        """Arm a specific group within a space."""
        from custom_components.ajax_cobranded.proto import arm_group_request_pb2 as pb

        request = pb.ArmSpaceGroupRequest(
            space_locator=self._make_space_locator(space_id),
            group_id=group_id,
            ignore_alarms=ignore_alarms,
        )
        response = await self._client.call_unary(
            _ARM_GROUP_METHOD, request, pb.ArmSpaceGroupResponse
        )
        if response.HasField("failure"):
            raise SecurityError(f"Arm group failed: {response.failure}")

    async def disarm_group(self, space_id: str, group_id: str) -> None:
        """Disarm a specific group within a space."""
        from custom_components.ajax_cobranded.proto import disarm_group_request_pb2 as pb

        request = pb.DisarmSpaceGroupRequest(
            space_locator=self._make_space_locator(space_id),
            group_id=group_id,
        )
        response = await self._client.call_unary(
            _DISARM_GROUP_METHOD, request, pb.DisarmSpaceGroupResponse
        )
        if response.HasField("failure"):
            raise SecurityError(f"Disarm group failed: {response.failure}")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/unit/test_spaces.py tests/unit/test_security.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add custom_components/ajax_cobranded/api/spaces.py \
    custom_components/ajax_cobranded/api/security.py \
    tests/unit/test_spaces.py tests/unit/test_security.py
git commit -m "feat(api): add spaces listing and security arm/disarm commands"
```

---

## Task 8: Devices API (Streaming and Commands)

**Files:**
- Create: `custom_components/ajax_cobranded/api/devices.py`
- Create: `tests/unit/test_devices.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for devices API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.models import BatteryInfo, Device
from custom_components.ajax_cobranded.const import DeviceState


class TestParseDevice:
    def test_parse_hub_device(self) -> None:
        """Parse a LightDevice containing a hub_device."""
        proto_device = MagicMock()
        proto_device.hub_device.common_device.profile.id = "dev-1"
        proto_device.hub_device.common_device.profile.name = "Front Door"
        proto_device.hub_device.common_device.profile.room_id = "room-1"
        proto_device.hub_device.common_device.profile.group_id = ""
        proto_device.hub_device.common_device.profile.malfunctions = 0
        proto_device.hub_device.common_device.profile.bypassed = False
        proto_device.hub_device.common_device.profile.device_marketing_id = "DoorProtect"
        proto_device.hub_device.common_device.profile.states = []
        proto_device.hub_device.common_device.profile.statuses = []
        proto_device.hub_device.common_device.hub_id = "hub-1"
        proto_device.hub_device.common_device.object_type.WhichOneof.return_value = "door_protect"
        proto_device.WhichOneof.return_value = "hub_device"

        device = DevicesApi.parse_device(proto_device)

        assert isinstance(device, Device)
        assert device.id == "dev-1"
        assert device.name == "Front Door"
        assert device.hub_id == "hub-1"
        assert device.device_type == "door_protect"
        assert device.room_id == "room-1"
        assert device.state == DeviceState.ONLINE

    def test_parse_offline_device(self) -> None:
        proto_device = MagicMock()
        proto_device.hub_device.common_device.profile.id = "dev-2"
        proto_device.hub_device.common_device.profile.name = "Motion"
        proto_device.hub_device.common_device.profile.room_id = ""
        proto_device.hub_device.common_device.profile.group_id = ""
        proto_device.hub_device.common_device.profile.malfunctions = 0
        proto_device.hub_device.common_device.profile.bypassed = False
        proto_device.hub_device.common_device.profile.device_marketing_id = "MotionProtect"
        # LIGHT_DEVICE_STATE_OFFLINE = 9
        state_mock = MagicMock()
        state_mock.__int__ = lambda self: 9
        state_mock.value = 9
        proto_device.hub_device.common_device.profile.states = [state_mock]
        proto_device.hub_device.common_device.profile.statuses = []
        proto_device.hub_device.common_device.hub_id = "hub-1"
        proto_device.hub_device.common_device.object_type.WhichOneof.return_value = (
            "motion_protect"
        )
        proto_device.WhichOneof.return_value = "hub_device"

        device = DevicesApi.parse_device(proto_device)
        assert device.state == DeviceState.OFFLINE

    def test_parse_non_hub_device_returns_none(self) -> None:
        """Non-hub devices (video_edge, smart_lock) return None for now."""
        proto_device = MagicMock()
        proto_device.WhichOneof.return_value = "video_edge"

        result = DevicesApi.parse_device(proto_device)
        assert result is None


class TestDevicesApiInit:
    def test_init(self) -> None:
        client = MagicMock()
        api = DevicesApi(client)
        assert api._client is client
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_devices.py -v`
Expected: FAIL — `devices` module not found.

- [ ] **Step 3: Implement devices.py**

```python
"""Devices API: streaming, parsing, and commands."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from custom_components.ajax_cobranded.api.models import BatteryInfo, Device, DeviceCommand
from custom_components.ajax_cobranded.const import DeviceState

if TYPE_CHECKING:
    from custom_components.ajax_cobranded.api.client import AjaxGrpcClient

_LOGGER = logging.getLogger(__name__)

# gRPC method paths
_STREAM_LIGHT_DEVICES = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".stream_light_devices.StreamLightDevicesService/execute"
)
_DEVICE_ON = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".device_command_device_on.DeviceCommandDeviceOnService/execute"
)
_DEVICE_OFF = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".device_command_device_off.DeviceCommandDeviceOffService/execute"
)
_DEVICE_BRIGHTNESS = (
    "/systems.ajax.api.ecosystem.v3.mobilegwsvc.service"
    ".device_command_brightness.DeviceCommandBrightnessService/execute"
)

# LightDeviceState enum mapping (from proto)
_STATE_MAP: dict[int, DeviceState] = {
    0: DeviceState.ONLINE,  # UNSPECIFIED = online (no negative state)
    1: DeviceState.LOCKED,
    2: DeviceState.SUSPENDED,
    3: DeviceState.UNKNOWN,  # ADDING_FAILED
    4: DeviceState.UNKNOWN,  # TRANSFERRING_FAILED
    5: DeviceState.ADDING,
    6: DeviceState.ADDING,  # TRANSFERRING
    7: DeviceState.BATTERY_SAVING,
    8: DeviceState.NOT_MIGRATED,
    9: DeviceState.OFFLINE,
    10: DeviceState.UPDATING,
    11: DeviceState.WALK_TEST,
}


class DevicesApi:
    """API operations for devices."""

    def __init__(self, client: AjaxGrpcClient) -> None:
        self._client = client

    @staticmethod
    def _parse_device_state(states: Any) -> DeviceState:
        """Parse the worst device state from the states list."""
        if not states:
            return DeviceState.ONLINE

        # Priority: OFFLINE > LOCKED > SUSPENDED > others > ONLINE
        worst = DeviceState.ONLINE
        priority = {
            DeviceState.OFFLINE: 100,
            DeviceState.LOCKED: 90,
            DeviceState.SUSPENDED: 80,
            DeviceState.UPDATING: 70,
            DeviceState.BATTERY_SAVING: 60,
            DeviceState.WALK_TEST: 50,
            DeviceState.ADDING: 40,
            DeviceState.NOT_MIGRATED: 30,
            DeviceState.UNKNOWN: 20,
            DeviceState.ONLINE: 0,
        }
        for s in states:
            val = s if isinstance(s, int) else int(s)
            mapped = _STATE_MAP.get(val, DeviceState.UNKNOWN)
            if priority.get(mapped, 0) > priority.get(worst, 0):
                worst = mapped
        return worst

    @staticmethod
    def _parse_battery(statuses: Any) -> BatteryInfo | None:
        """Extract battery info from device statuses."""
        for status in statuses:
            which = status.WhichOneof("status") if hasattr(status, "WhichOneof") else None
            if which == "battery":
                return BatteryInfo(
                    level=status.battery.charge_level_percentage,
                    is_low=status.battery.state != 0,  # 0 = OK
                )
        return None

    @staticmethod
    def _parse_statuses(statuses: Any) -> dict[str, Any]:
        """Extract status flags from device statuses into a flat dict."""
        result: dict[str, Any] = {}
        for status in statuses:
            which = status.WhichOneof("status") if hasattr(status, "WhichOneof") else None
            if which is None:
                continue
            if which == "door_opened":
                result["door_opened"] = True
            elif which == "motion_detected":
                result["motion_detected"] = True
            elif which == "smoke_detected":
                result["smoke_detected"] = True
            elif which == "co_level_detected":
                result["co_detected"] = True
            elif which == "high_temperature_detected":
                result["high_temperature"] = True
            elif which == "leak_detected":
                result["leak_detected"] = True
            elif which == "tamper":
                result["tamper"] = True
            elif which == "temperature":
                result["temperature"] = status.temperature.value
            elif which == "life_quality":
                lq = status.life_quality
                if hasattr(lq, "temperature"):
                    result["temperature"] = lq.temperature
                if hasattr(lq, "humidity"):
                    result["humidity"] = lq.humidity
                if hasattr(lq, "co2"):
                    result["co2"] = lq.co2
            elif which == "signal_strength":
                result["signal_strength"] = status.signal_strength.value
        return result

    @staticmethod
    def parse_device(proto_light_device: Any) -> Device | None:
        """Parse a LightDevice proto into a Device model. Returns None for unsupported types."""
        device_kind = proto_light_device.WhichOneof("device")
        if device_kind != "hub_device":
            _LOGGER.debug("Skipping non-hub device type: %s", device_kind)
            return None

        hub_dev = proto_light_device.hub_device
        common = hub_dev.common_device
        profile = common.profile

        device_type = common.object_type.WhichOneof("type") or "unknown"

        return Device(
            id=profile.id,
            hub_id=common.hub_id,
            name=profile.name,
            device_type=device_type,
            room_id=profile.room_id if profile.room_id else None,
            group_id=profile.group_id if profile.group_id else None,
            state=DevicesApi._parse_device_state(profile.states),
            malfunctions=profile.malfunctions,
            bypassed=profile.bypassed,
            statuses=DevicesApi._parse_statuses(profile.statuses),
            battery=DevicesApi._parse_battery(profile.statuses),
        )

    async def send_command(self, command: DeviceCommand) -> None:
        """Send a device command (on/off/brightness)."""
        if command.action == "on":
            await self._send_on_off(command, on=True)
        elif command.action == "off":
            await self._send_on_off(command, on=False)
        elif command.action == "brightness":
            await self._send_brightness(command)

    async def _send_on_off(self, command: DeviceCommand, *, on: bool) -> None:
        """Send on or off command."""
        if on:
            from custom_components.ajax_cobranded.proto import device_command_device_on_pb2 as pb

            method = _DEVICE_ON
            channel_enum = pb.DeviceCommandDeviceOnRequest.Channel
            request = pb.DeviceCommandDeviceOnRequest(
                hub_id=command.hub_id,
                device_id=command.device_id,
                channels=[channel_enum.Value(f"CHANNEL_{c}") for c in command.channels],
            )
            resp_type = pb.DeviceCommandDeviceOnResponse
        else:
            from custom_components.ajax_cobranded.proto import device_command_device_off_pb2 as pb

            method = _DEVICE_OFF
            channel_enum = pb.DeviceCommandDeviceOffRequest.Channel
            request = pb.DeviceCommandDeviceOffRequest(
                hub_id=command.hub_id,
                device_id=command.device_id,
                channels=[channel_enum.Value(f"CHANNEL_{c}") for c in command.channels],
            )
            resp_type = pb.DeviceCommandDeviceOffResponse

        response = await self._client.call_unary(method, request, resp_type)
        if response.HasField("failure"):
            _LOGGER.error("Device %s command failed: %s", "on" if on else "off", response.failure)

    async def _send_brightness(self, command: DeviceCommand) -> None:
        """Send brightness command."""
        from custom_components.ajax_cobranded.proto import device_command_brightness_pb2 as pb

        channel_enum = pb.DeviceCommandBrightnessRequest.Channel
        request = pb.DeviceCommandBrightnessRequest(
            hub_id=command.hub_id,
            device_id=command.device_id,
            brightness_in_percentage=command.brightness or 0,
            channels=[channel_enum.Value(f"CHANNEL_{c}") for c in command.channels],
            brightness_type=pb.DeviceCommandBrightnessRequest.BRIGHTNESS_TYPE_ABSOLUTE,
        )
        response = await self._client.call_unary(
            _DEVICE_BRIGHTNESS, request, pb.DeviceCommandBrightnessResponse
        )
        if response.HasField("failure"):
            _LOGGER.error("Brightness command failed: %s", response.failure)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_devices.py -v`
Expected: All PASS.

- [ ] **Step 5: Update api/__init__.py with public exports**

```python
"""Ajax Security API client."""

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.models import (
    BatteryInfo,
    Device,
    DeviceCommand,
    Space,
)
from custom_components.ajax_cobranded.api.security import SecurityApi, SecurityError
from custom_components.ajax_cobranded.api.session import (
    AjaxSession,
    AuthenticationError,
    TwoFactorRequired,
)
from custom_components.ajax_cobranded.api.spaces import SpacesApi

__all__ = [
    "AjaxGrpcClient",
    "AjaxSession",
    "AuthenticationError",
    "BatteryInfo",
    "Device",
    "DeviceCommand",
    "DevicesApi",
    "SecurityApi",
    "SecurityError",
    "Space",
    "SpacesApi",
    "TwoFactorRequired",
]
```

- [ ] **Step 6: Commit**

```bash
git add custom_components/ajax_cobranded/api/ tests/unit/test_devices.py
git commit -m "feat(api): add device streaming, parsing, and command execution"
```

---

## Task 9: HA Integration Setup and Config Flow

**Files:**
- Create: `custom_components/ajax_cobranded/manifest.json`
- Create: `custom_components/ajax_cobranded/config_flow.py`
- Modify: `custom_components/ajax_cobranded/__init__.py`
- Create: `custom_components/ajax_cobranded/strings.json`
- Create: `custom_components/ajax_cobranded/translations/es.json`
- Create: `custom_components/ajax_cobranded/translations/ca.json`
- Create: `tests/unit/test_config_flow.py`

- [ ] **Step 1: Create manifest.json**

```json
{
    "domain": "ajax_cobranded",
    "name": "Ajax Security",
    "codeowners": [],
    "config_flow": true,
    "dependencies": [],
    "documentation": "https://github.com/YOUR_USERNAME/ajax-cobranded-hass",
    "integration_type": "hub",
    "iot_class": "cloud_push",
    "requirements": ["grpcio>=1.60.0", "protobuf>=4.25.0"],
    "version": "0.1.0"
}
```

- [ ] **Step 2: Create strings.json**

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Ajax Security Login",
                "description": "Enter your Ajax/Protegim account credentials.",
                "data": {
                    "email": "Email",
                    "password": "Password"
                }
            },
            "2fa": {
                "title": "Two-Factor Authentication",
                "description": "Enter the 6-digit code from your authenticator app.",
                "data": {
                    "totp_code": "TOTP Code"
                }
            },
            "select_spaces": {
                "title": "Select Spaces",
                "description": "Choose which spaces (hubs) to add.",
                "data": {
                    "spaces": "Spaces"
                }
            }
        },
        "error": {
            "invalid_auth": "Invalid email or password.",
            "invalid_totp": "Invalid TOTP code. Please try again.",
            "cannot_connect": "Cannot connect to Ajax servers.",
            "unknown": "An unexpected error occurred."
        },
        "abort": {
            "already_configured": "This account is already configured.",
            "account_locked": "Account is locked. Please try again later.",
            "reauth_successful": "Re-authentication successful."
        }
    },
    "options": {
        "step": {
            "init": {
                "title": "Ajax Security Options",
                "data": {
                    "poll_interval": "Fallback poll interval (seconds)",
                    "use_pin_code": "Require PIN code for arm/disarm"
                }
            }
        }
    }
}
```

- [ ] **Step 3: Create translations/es.json**

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Inicio de sesion Ajax Security",
                "description": "Introduce las credenciales de tu cuenta Ajax/Protegim.",
                "data": {
                    "email": "Correo electronico",
                    "password": "Contrasena"
                }
            },
            "2fa": {
                "title": "Autenticacion de dos factores",
                "description": "Introduce el codigo de 6 digitos de tu app de autenticacion.",
                "data": {
                    "totp_code": "Codigo TOTP"
                }
            },
            "select_spaces": {
                "title": "Seleccionar espacios",
                "description": "Elige que espacios (hubs) anadir.",
                "data": {
                    "spaces": "Espacios"
                }
            }
        },
        "error": {
            "invalid_auth": "Correo o contrasena incorrectos.",
            "invalid_totp": "Codigo TOTP incorrecto. Intentalo de nuevo.",
            "cannot_connect": "No se puede conectar a los servidores de Ajax.",
            "unknown": "Ha ocurrido un error inesperado."
        },
        "abort": {
            "already_configured": "Esta cuenta ya esta configurada.",
            "account_locked": "Cuenta bloqueada. Intentalo mas tarde.",
            "reauth_successful": "Reautenticacion exitosa."
        }
    }
}
```

- [ ] **Step 4: Create translations/ca.json**

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Inici de sessio Ajax Security",
                "description": "Introdueix les credencials del teu compte Ajax/Protegim.",
                "data": {
                    "email": "Correu electronic",
                    "password": "Contrasenya"
                }
            },
            "2fa": {
                "title": "Autenticacio de dos factors",
                "description": "Introdueix el codi de 6 digits de la teva app d'autenticacio.",
                "data": {
                    "totp_code": "Codi TOTP"
                }
            },
            "select_spaces": {
                "title": "Seleccionar espais",
                "description": "Tria quins espais (hubs) afegir.",
                "data": {
                    "spaces": "Espais"
                }
            }
        },
        "error": {
            "invalid_auth": "Correu o contrasenya incorrectes.",
            "invalid_totp": "Codi TOTP incorrecte. Torna-ho a provar.",
            "cannot_connect": "No es pot connectar als servidors d'Ajax.",
            "unknown": "S'ha produit un error inesperat."
        },
        "abort": {
            "already_configured": "Aquest compte ja esta configurat.",
            "account_locked": "Compte bloquejat. Torna-ho a provar mes tard.",
            "reauth_successful": "Reautenticacio correcta."
        }
    }
}
```

- [ ] **Step 5: Write failing tests for config_flow**

```python
"""Tests for config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.config_flow import AjaxProtegimConfigFlow
from custom_components.ajax_cobranded.const import DOMAIN


class TestConfigFlowInit:
    def test_domain(self) -> None:
        flow = AjaxProtegimConfigFlow()
        assert flow.DOMAIN == DOMAIN

    def test_has_user_step(self) -> None:
        flow = AjaxProtegimConfigFlow()
        assert hasattr(flow, "async_step_user")

    def test_has_2fa_step(self) -> None:
        flow = AjaxProtegimConfigFlow()
        assert hasattr(flow, "async_step_2fa")

    def test_has_select_spaces_step(self) -> None:
        flow = AjaxProtegimConfigFlow()
        assert hasattr(flow, "async_step_select_spaces")
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/unit/test_config_flow.py -v`
Expected: FAIL — module not found.

- [ ] **Step 7: Implement config_flow.py**

```python
"""Config flow for Ajax Security integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.session import AuthenticationError, TwoFactorRequired
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)

TOTP_SCHEMA = vol.Schema(
    {
        vol.Required("totp_code"): str,
    }
)


class AjaxProtegimConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ajax Security."""

    VERSION = 1
    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize."""
        self._client: AjaxGrpcClient | None = None
        self._email: str = ""
        self._password: str = ""
        self._request_id: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial credentials step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email = user_input["email"]
            self._password = user_input["password"]

            await self.async_set_unique_id(self._email)
            self._abort_if_unique_id_configured()

            try:
                self._client = AjaxGrpcClient(
                    email=self._email, password=self._password
                )
                await self._client.connect()
                # Attempt login - will be implemented when proto stubs are ready
                # For now, proceed to space selection
                return await self.async_step_select_spaces()
            except TwoFactorRequired as e:
                self._request_id = e.request_id
                return await self.async_step_2fa()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except (ConnectionError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    async def async_step_2fa(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the 2FA step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # 2FA verification will be implemented with proto stubs
                return await self.async_step_select_spaces()
            except AuthenticationError:
                errors["base"] = "invalid_totp"
            except Exception:
                _LOGGER.exception("Unexpected error during 2FA")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="2fa",
            data_schema=TOTP_SCHEMA,
            errors=errors,
        )

    async def async_step_select_spaces(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle space selection step."""
        if user_input is not None:
            assert self._client is not None
            return self.async_create_entry(
                title=f"Ajax Security ({self._email})",
                data={
                    "email": self._email,
                    "password": self._password,
                    "spaces": user_input["spaces"],
                    "session_token": self._client.session.session_token,
                    "user_hex_id": self._client.session.user_hex_id,
                    "device_id": self._client.session.device_id,
                },
            )

        # Fetch available spaces
        if self._client:
            spaces_api = SpacesApi(self._client)
            spaces = await spaces_api.list_spaces()
            space_options = {s.id: s.name for s in spaces}
        else:
            space_options = {}

        return self.async_show_form(
            step_id="select_spaces",
            data_schema=vol.Schema(
                {
                    vol.Required("spaces"): vol.All(
                        vol.Coerce(list), [vol.In(space_options)]
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> AjaxProtegimOptionsFlow:
        return AjaxProtegimOptionsFlow(config_entry)


class AjaxProtegimOptionsFlow(OptionsFlow):
    """Handle options for Ajax Security."""

    def __init__(self, config_entry: Any) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "poll_interval",
                        default=self._config_entry.options.get(
                            "poll_interval", DEFAULT_POLL_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=30, max=300)),
                    vol.Optional(
                        "use_pin_code",
                        default=self._config_entry.options.get("use_pin_code", False),
                    ): bool,
                }
            ),
        )
```

- [ ] **Step 8: Implement __init__.py (integration setup)**

```python
"""Ajax Security Home Assistant integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.const import DOMAIN
from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
]

type AjaxProtegimConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: AjaxProtegimConfigEntry) -> bool:
    """Set up Ajax Security from a config entry."""
    client = AjaxGrpcClient(
        email=entry.data["email"],
        password=entry.data["password"],
        device_id=entry.data.get("device_id"),
    )

    # Restore session if available
    if entry.data.get("session_token") and entry.data.get("user_hex_id"):
        client.session.set_session(
            entry.data["session_token"],
            entry.data["user_hex_id"],
        )

    await client.connect()

    coordinator = AjaxProtegimCoordinator(
        hass=hass,
        client=client,
        space_ids=entry.data.get("spaces", []),
        poll_interval=entry.options.get("poll_interval", 30),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: AjaxProtegimConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: AjaxProtegimCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok
```

- [ ] **Step 9: Run tests to verify they pass**

Run: `pytest tests/unit/test_config_flow.py -v`
Expected: All PASS.

- [ ] **Step 10: Commit**

```bash
git add custom_components/ajax_cobranded/manifest.json \
    custom_components/ajax_cobranded/strings.json \
    custom_components/ajax_cobranded/translations/ \
    custom_components/ajax_cobranded/config_flow.py \
    custom_components/ajax_cobranded/__init__.py \
    tests/unit/test_config_flow.py
git commit -m "feat(ha): add config flow with 2FA support and integration setup"
```

---

## Task 10: DataUpdateCoordinator

**Files:**
- Create: `custom_components/ajax_cobranded/coordinator.py`
- Create: `tests/unit/test_coordinator.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for the data update coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ajax_cobranded.api.models import Device, Space
from custom_components.ajax_cobranded.const import ConnectionStatus, DeviceState, SecurityState


class TestCoordinatorInit:
    def test_attributes(self) -> None:
        from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

        hass = MagicMock()
        client = MagicMock()
        coordinator = AjaxProtegimCoordinator(
            hass=hass, client=client, space_ids=["s1"], poll_interval=30
        )
        assert coordinator._client is client
        assert coordinator._space_ids == ["s1"]

    def test_data_structure(self) -> None:
        from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

        hass = MagicMock()
        client = MagicMock()
        coordinator = AjaxProtegimCoordinator(
            hass=hass, client=client, space_ids=["s1"], poll_interval=30
        )
        assert coordinator.spaces == {}
        assert coordinator.devices == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_coordinator.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement coordinator.py**

```python
"""Data update coordinator for Ajax Security."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.devices import DevicesApi
from custom_components.ajax_cobranded.api.models import Device, Space
from custom_components.ajax_cobranded.api.security import SecurityApi
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AjaxProtegimCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that manages data refresh via gRPC streams with polling fallback."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AjaxGrpcClient,
        space_ids: list[str],
        poll_interval: int = 30,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self._client = client
        self._space_ids = space_ids
        self._spaces_api = SpacesApi(client)
        self._security_api = SecurityApi(client)
        self._devices_api = DevicesApi(client)
        self.spaces: dict[str, Space] = {}
        self.devices: dict[str, Device] = {}

    @property
    def security_api(self) -> SecurityApi:
        return self._security_api

    @property
    def devices_api(self) -> DevicesApi:
        return self._devices_api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Ajax API."""
        try:
            # Refresh spaces
            all_spaces = await self._spaces_api.list_spaces()
            self.spaces = {
                s.id: s for s in all_spaces if s.id in self._space_ids
            }

            # TODO: Implement device streaming in future task
            # For now, this is the polling fallback path

            return {"spaces": self.spaces, "devices": self.devices}
        except Exception as err:
            raise UpdateFailed(f"Error fetching Ajax data: {err}") from err

    async def async_shutdown(self) -> None:
        """Clean up resources."""
        await self._client.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_coordinator.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajax_cobranded/coordinator.py tests/unit/test_coordinator.py
git commit -m "feat(ha): add DataUpdateCoordinator with polling fallback"
```

---

## Task 11: Alarm Control Panel Entity

**Files:**
- Create: `custom_components/ajax_cobranded/alarm_control_panel.py`
- Create: `tests/unit/test_alarm_control_panel.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for alarm control panel entity."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.alarm_control_panel import (
    AjaxAlarmControlPanel,
    map_security_state,
)
from custom_components.ajax_cobranded.const import ConnectionStatus, SecurityState


class TestMapSecurityState:
    def test_armed(self) -> None:
        from homeassistant.const import STATE_ALARM_ARMED_AWAY

        assert map_security_state(SecurityState.ARMED) == STATE_ALARM_ARMED_AWAY

    def test_disarmed(self) -> None:
        from homeassistant.const import STATE_ALARM_DISARMED

        assert map_security_state(SecurityState.DISARMED) == STATE_ALARM_DISARMED

    def test_night_mode(self) -> None:
        from homeassistant.const import STATE_ALARM_ARMED_NIGHT

        assert map_security_state(SecurityState.NIGHT_MODE) == STATE_ALARM_ARMED_NIGHT

    def test_partially_armed(self) -> None:
        from homeassistant.const import STATE_ALARM_ARMED_CUSTOM_BYPASS

        assert (
            map_security_state(SecurityState.PARTIALLY_ARMED)
            == STATE_ALARM_ARMED_CUSTOM_BYPASS
        )

    def test_arming_states(self) -> None:
        from homeassistant.const import STATE_ALARM_ARMING

        assert map_security_state(SecurityState.AWAITING_EXIT_TIMER) == STATE_ALARM_ARMING
        assert map_security_state(SecurityState.AWAITING_SECOND_STAGE) == STATE_ALARM_ARMING


class TestAlarmControlPanel:
    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        panel = AjaxAlarmControlPanel(coordinator=coordinator, space_id="s1")
        assert panel.unique_id == "ajax_cobranded_alarm_s1"

    def test_available_when_online(self) -> None:
        from custom_components.ajax_cobranded.api.models import Space

        coordinator = MagicMock()
        coordinator.spaces = {
            "s1": Space(
                id="s1",
                hub_id="h1",
                name="Home",
                security_state=SecurityState.DISARMED,
                connection_status=ConnectionStatus.ONLINE,
                malfunctions_count=0,
            )
        }
        panel = AjaxAlarmControlPanel(coordinator=coordinator, space_id="s1")
        assert panel.available is True

    def test_unavailable_when_offline(self) -> None:
        from custom_components.ajax_cobranded.api.models import Space

        coordinator = MagicMock()
        coordinator.spaces = {
            "s1": Space(
                id="s1",
                hub_id="h1",
                name="Home",
                security_state=SecurityState.DISARMED,
                connection_status=ConnectionStatus.OFFLINE,
                malfunctions_count=0,
            )
        }
        panel = AjaxAlarmControlPanel(coordinator=coordinator, space_id="s1")
        assert panel.available is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_alarm_control_panel.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement alarm_control_panel.py**

```python
"""Alarm control panel for Ajax Security."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import DOMAIN, SecurityState
from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

_LOGGER = logging.getLogger(__name__)

_STATE_MAP = {
    SecurityState.ARMED: STATE_ALARM_ARMED_AWAY,
    SecurityState.DISARMED: STATE_ALARM_DISARMED,
    SecurityState.NIGHT_MODE: STATE_ALARM_ARMED_NIGHT,
    SecurityState.PARTIALLY_ARMED: STATE_ALARM_ARMED_CUSTOM_BYPASS,
    SecurityState.AWAITING_EXIT_TIMER: STATE_ALARM_ARMING,
    SecurityState.AWAITING_SECOND_STAGE: STATE_ALARM_ARMING,
    SecurityState.TWO_STAGE_INCOMPLETE: STATE_ALARM_ARMING,
    SecurityState.AWAITING_VDS: STATE_ALARM_ARMING,
    SecurityState.NONE: STATE_ALARM_DISARMED,
}


def map_security_state(state: SecurityState) -> str:
    """Map Ajax security state to HA alarm state."""
    return _STATE_MAP.get(state, STATE_ALARM_DISARMED)


async def async_setup_entry(
    hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up alarm control panels."""
    coordinator: AjaxProtegimCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        AjaxAlarmControlPanel(coordinator=coordinator, space_id=space_id)
        for space_id in coordinator.spaces
    ]
    async_add_entities(entities)


class AjaxAlarmControlPanel(
    CoordinatorEntity[AjaxProtegimCoordinator], AlarmControlPanelEntity
):
    """Ajax alarm control panel entity."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, coordinator: AjaxProtegimCoordinator, space_id: str) -> None:
        super().__init__(coordinator)
        self._space_id = space_id
        self._attr_unique_id = f"ajax_cobranded_alarm_{space_id}"

    @property
    def _space(self) -> Any | None:
        return self.coordinator.spaces.get(self._space_id)

    @property
    def name(self) -> str:
        space = self._space
        return space.name if space else "Ajax Alarm"

    @property
    def available(self) -> bool:
        space = self._space
        return space is not None and space.is_online

    @property
    def alarm_state(self) -> str | None:
        space = self._space
        if space is None:
            return None
        return map_security_state(space.security_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        space = self._space
        if space is None:
            return {}
        return {
            "hub_id": space.hub_id,
            "malfunctions": space.malfunctions_count,
            "connection_status": space.connection_status.name,
        }

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self.coordinator.security_api.arm(self._space_id)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self.coordinator.security_api.arm_night_mode(self._space_id)
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self.coordinator.security_api.disarm(self._space_id)
        await self.coordinator.async_request_refresh()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_alarm_control_panel.py -v`
Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add custom_components/ajax_cobranded/alarm_control_panel.py \
    tests/unit/test_alarm_control_panel.py
git commit -m "feat(ha): add alarm control panel entity with arm/disarm/night mode"
```

---

## Task 12: Binary Sensor and Sensor Entities

**Files:**
- Create: `custom_components/ajax_cobranded/binary_sensor.py`
- Create: `custom_components/ajax_cobranded/sensor.py`
- Create: `tests/unit/test_binary_sensor.py`
- Create: `tests/unit/test_sensor.py`

- [ ] **Step 1: Write failing tests for binary_sensor**

```python
"""Tests for binary sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.ajax_cobranded.binary_sensor import (
    BINARY_SENSOR_TYPES,
    AjaxBinarySensor,
)
from custom_components.ajax_cobranded.api.models import BatteryInfo, Device
from custom_components.ajax_cobranded.const import DeviceState


class TestBinarySensorTypes:
    def test_door_sensor_type_exists(self) -> None:
        assert "door_opened" in BINARY_SENSOR_TYPES

    def test_motion_sensor_type_exists(self) -> None:
        assert "motion_detected" in BINARY_SENSOR_TYPES

    def test_smoke_sensor_type_exists(self) -> None:
        assert "smoke_detected" in BINARY_SENSOR_TYPES

    def test_leak_sensor_type_exists(self) -> None:
        assert "leak_detected" in BINARY_SENSOR_TYPES

    def test_tamper_sensor_type_exists(self) -> None:
        assert "tamper" in BINARY_SENSOR_TYPES


class TestAjaxBinarySensor:
    def _make_device(self, statuses: dict) -> Device:
        return Device(
            id="dev-1",
            hub_id="hub-1",
            name="Front Door",
            device_type="door_protect",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses=statuses,
            battery=None,
        )

    def test_is_on_true(self) -> None:
        device = self._make_device({"door_opened": True})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}

        sensor = AjaxBinarySensor(
            coordinator=coordinator,
            device_id="dev-1",
            status_key="door_opened",
        )
        assert sensor.is_on is True

    def test_is_on_false_when_key_absent(self) -> None:
        device = self._make_device({})
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}

        sensor = AjaxBinarySensor(
            coordinator=coordinator,
            device_id="dev-1",
            status_key="door_opened",
        )
        assert sensor.is_on is False

    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": self._make_device({})}
        sensor = AjaxBinarySensor(
            coordinator=coordinator,
            device_id="dev-1",
            status_key="door_opened",
        )
        assert sensor.unique_id == "ajax_cobranded_dev-1_door_opened"
```

- [ ] **Step 2: Write failing tests for sensor**

```python
"""Tests for sensor entities."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.ajax_cobranded.sensor import SENSOR_TYPES, AjaxSensor
from custom_components.ajax_cobranded.api.models import BatteryInfo, Device
from custom_components.ajax_cobranded.const import DeviceState


class TestSensorTypes:
    def test_battery_type_exists(self) -> None:
        assert "battery_level" in SENSOR_TYPES

    def test_temperature_type_exists(self) -> None:
        assert "temperature" in SENSOR_TYPES

    def test_humidity_type_exists(self) -> None:
        assert "humidity" in SENSOR_TYPES


class TestAjaxSensor:
    def test_battery_level(self) -> None:
        device = Device(
            id="dev-1",
            hub_id="hub-1",
            name="Motion",
            device_type="motion_protect",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={},
            battery=BatteryInfo(level=85, is_low=False),
        )
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}

        sensor = AjaxSensor(
            coordinator=coordinator,
            device_id="dev-1",
            sensor_key="battery_level",
        )
        assert sensor.native_value == 85

    def test_temperature(self) -> None:
        device = Device(
            id="dev-1",
            hub_id="hub-1",
            name="LifeQuality",
            device_type="life_quality",
            room_id=None,
            group_id=None,
            state=DeviceState.ONLINE,
            malfunctions=0,
            bypassed=False,
            statuses={"temperature": 22.5},
            battery=None,
        )
        coordinator = MagicMock()
        coordinator.devices = {"dev-1": device}

        sensor = AjaxSensor(
            coordinator=coordinator,
            device_id="dev-1",
            sensor_key="temperature",
        )
        assert sensor.native_value == 22.5
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_binary_sensor.py tests/unit/test_sensor.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 4: Implement binary_sensor.py**

```python
"""Binary sensor entities for Ajax Security."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import DOMAIN
from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BinarySensorTypeInfo:
    """Describes a binary sensor type."""

    device_class: BinarySensorDeviceClass
    name_suffix: str


BINARY_SENSOR_TYPES: dict[str, BinarySensorTypeInfo] = {
    "door_opened": BinarySensorTypeInfo(BinarySensorDeviceClass.DOOR, "Door"),
    "motion_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.MOTION, "Motion"),
    "smoke_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.SMOKE, "Smoke"),
    "leak_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.MOISTURE, "Leak"),
    "tamper": BinarySensorTypeInfo(BinarySensorDeviceClass.TAMPER, "Tamper"),
    "co_detected": BinarySensorTypeInfo(BinarySensorDeviceClass.CO, "CO"),
    "high_temperature": BinarySensorTypeInfo(BinarySensorDeviceClass.HEAT, "Heat"),
}

# Which device types produce which status keys
_DEVICE_TYPE_SENSORS: dict[str, list[str]] = {
    "door_protect": ["door_opened", "tamper"],
    "door_protect_plus": ["door_opened", "tamper"],
    "door_protect_fibra": ["door_opened", "tamper"],
    "motion_protect": ["motion_detected", "tamper"],
    "motion_protect_plus": ["motion_detected", "tamper"],
    "motion_cam": ["motion_detected", "tamper"],
    "motion_cam_outdoor": ["motion_detected", "tamper"],
    "combi_protect": ["motion_detected", "tamper"],
    "fire_protect": ["smoke_detected", "high_temperature", "tamper"],
    "fire_protect_2": ["smoke_detected", "co_detected", "high_temperature", "tamper"],
    "fire_protect_plus": ["smoke_detected", "co_detected", "high_temperature", "tamper"],
    "leaks_protect": ["leak_detected", "tamper"],
    "glass_protect": ["tamper"],
}


async def async_setup_entry(
    hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors."""
    coordinator: AjaxProtegimCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AjaxBinarySensor] = []
    for device_id, device in coordinator.devices.items():
        sensor_keys = _DEVICE_TYPE_SENSORS.get(device.device_type, ["tamper"])
        for key in sensor_keys:
            if key in BINARY_SENSOR_TYPES:
                entities.append(
                    AjaxBinarySensor(
                        coordinator=coordinator,
                        device_id=device_id,
                        status_key=key,
                    )
                )

    async_add_entities(entities)


class AjaxBinarySensor(
    CoordinatorEntity[AjaxProtegimCoordinator], BinarySensorEntity
):
    """Ajax binary sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AjaxProtegimCoordinator,
        device_id: str,
        status_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._status_key = status_key
        self._type_info = BINARY_SENSOR_TYPES[status_key]
        self._attr_unique_id = f"ajax_cobranded_{device_id}_{status_key}"
        self._attr_device_class = self._type_info.device_class

    @property
    def _device(self) -> Any | None:
        return self.coordinator.devices.get(self._device_id)

    @property
    def name(self) -> str:
        device = self._device
        base = device.name if device else "Device"
        return f"{base} {self._type_info.name_suffix}"

    @property
    def available(self) -> bool:
        device = self._device
        return device is not None and device.is_online

    @property
    def is_on(self) -> bool:
        device = self._device
        if device is None:
            return False
        return bool(device.statuses.get(self._status_key, False))
```

- [ ] **Step 5: Implement sensor.py**

```python
"""Sensor entities for Ajax Security."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.const import DOMAIN
from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SensorTypeInfo:
    """Describes a sensor type."""

    device_class: SensorDeviceClass | None
    state_class: SensorStateClass
    unit: str | None
    name_suffix: str
    value_source: str  # "status" or "battery"


SENSOR_TYPES: dict[str, SensorTypeInfo] = {
    "battery_level": SensorTypeInfo(
        SensorDeviceClass.BATTERY,
        SensorStateClass.MEASUREMENT,
        PERCENTAGE,
        "Battery",
        "battery",
    ),
    "temperature": SensorTypeInfo(
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
        UnitOfTemperature.CELSIUS,
        "Temperature",
        "status",
    ),
    "humidity": SensorTypeInfo(
        SensorDeviceClass.HUMIDITY,
        SensorStateClass.MEASUREMENT,
        PERCENTAGE,
        "Humidity",
        "status",
    ),
    "co2": SensorTypeInfo(
        SensorDeviceClass.CO2,
        SensorStateClass.MEASUREMENT,
        "ppm",
        "CO2",
        "status",
    ),
    "signal_strength": SensorTypeInfo(
        SensorDeviceClass.SIGNAL_STRENGTH,
        SensorStateClass.MEASUREMENT,
        "dBm",
        "Signal",
        "status",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors."""
    coordinator: AjaxProtegimCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AjaxSensor] = []
    for device_id, device in coordinator.devices.items():
        # Battery sensor for all devices with battery
        if device.battery is not None:
            entities.append(
                AjaxSensor(coordinator=coordinator, device_id=device_id, sensor_key="battery_level")
            )
        # Status-based sensors
        for key in ("temperature", "humidity", "co2", "signal_strength"):
            if key in device.statuses:
                entities.append(
                    AjaxSensor(coordinator=coordinator, device_id=device_id, sensor_key=key)
                )

    async_add_entities(entities)


class AjaxSensor(CoordinatorEntity[AjaxProtegimCoordinator], SensorEntity):
    """Ajax sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AjaxProtegimCoordinator,
        device_id: str,
        sensor_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._sensor_key = sensor_key
        self._type_info = SENSOR_TYPES[sensor_key]
        self._attr_unique_id = f"ajax_cobranded_{device_id}_{sensor_key}"
        self._attr_device_class = self._type_info.device_class
        self._attr_state_class = self._type_info.state_class
        self._attr_native_unit_of_measurement = self._type_info.unit

    @property
    def _device(self) -> Any | None:
        return self.coordinator.devices.get(self._device_id)

    @property
    def name(self) -> str:
        device = self._device
        base = device.name if device else "Device"
        return f"{base} {self._type_info.name_suffix}"

    @property
    def available(self) -> bool:
        device = self._device
        return device is not None and device.is_online

    @property
    def native_value(self) -> float | int | None:
        device = self._device
        if device is None:
            return None

        if self._type_info.value_source == "battery" and device.battery:
            return device.battery.level

        return device.statuses.get(self._sensor_key)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/unit/test_binary_sensor.py tests/unit/test_sensor.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add custom_components/ajax_cobranded/binary_sensor.py \
    custom_components/ajax_cobranded/sensor.py \
    tests/unit/test_binary_sensor.py tests/unit/test_sensor.py
git commit -m "feat(ha): add binary sensor and sensor entities"
```

---

## Task 13: Switch and Light Entities

**Files:**
- Create: `custom_components/ajax_cobranded/switch.py`
- Create: `custom_components/ajax_cobranded/light.py`
- Create: `tests/unit/test_switch.py`
- Create: `tests/unit/test_light.py`

- [ ] **Step 1: Write failing tests for switch**

```python
"""Tests for switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.switch import AjaxSwitch, SWITCH_DEVICE_TYPES
from custom_components.ajax_cobranded.api.models import Device
from custom_components.ajax_cobranded.const import DeviceState


class TestSwitchDeviceTypes:
    def test_relay_is_switch(self) -> None:
        assert "relay" in SWITCH_DEVICE_TYPES

    def test_wall_switch_is_switch(self) -> None:
        assert "wall_switch" in SWITCH_DEVICE_TYPES

    def test_socket_is_switch(self) -> None:
        assert "socket" in SWITCH_DEVICE_TYPES


class TestAjaxSwitch:
    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1",
            device_type="relay", channel=1,
        )
        assert sw.unique_id == "ajax_cobranded_d1_switch_1"

    def test_turn_on_calls_command(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1",
            device_type="relay", channel=1,
        )
        assert hasattr(sw, "async_turn_on")

    def test_turn_off_calls_command(self) -> None:
        coordinator = MagicMock()
        coordinator.devices_api.send_command = AsyncMock()
        sw = AjaxSwitch(
            coordinator=coordinator, device_id="d1", hub_id="h1",
            device_type="relay", channel=1,
        )
        assert hasattr(sw, "async_turn_off")
```

- [ ] **Step 2: Write failing tests for light**

```python
"""Tests for light entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ajax_cobranded.light import AjaxLight, LIGHT_DEVICE_TYPES


class TestLightDeviceTypes:
    def test_dimmer_is_light(self) -> None:
        assert "light_switch_dimmer" in LIGHT_DEVICE_TYPES


class TestAjaxLight:
    def test_unique_id(self) -> None:
        coordinator = MagicMock()
        light = AjaxLight(
            coordinator=coordinator, device_id="d1", hub_id="h1",
            device_type="light_switch_dimmer", channel=1,
        )
        assert light.unique_id == "ajax_cobranded_d1_light_1"

    def test_has_brightness_support(self) -> None:
        from homeassistant.components.light import ColorMode

        coordinator = MagicMock()
        light = AjaxLight(
            coordinator=coordinator, device_id="d1", hub_id="h1",
            device_type="light_switch_dimmer", channel=1,
        )
        assert ColorMode.BRIGHTNESS in light.supported_color_modes
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_switch.py tests/unit/test_light.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 4: Implement switch.py**

```python
"""Switch entities for Ajax Security."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.api.models import DeviceCommand
from custom_components.ajax_cobranded.const import DOMAIN
from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

_LOGGER = logging.getLogger(__name__)

SWITCH_DEVICE_TYPES: dict[str, int] = {
    "relay": 1,
    "wall_switch": 1,
    "socket": 1,
    "light_switch": 1,
    "light_switch_two_gang": 2,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up switches."""
    coordinator: AjaxProtegimCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AjaxSwitch] = []
    for device_id, device in coordinator.devices.items():
        num_channels = SWITCH_DEVICE_TYPES.get(device.device_type, 0)
        for ch in range(1, num_channels + 1):
            entities.append(
                AjaxSwitch(
                    coordinator=coordinator,
                    device_id=device_id,
                    hub_id=device.hub_id,
                    device_type=device.device_type,
                    channel=ch,
                )
            )

    async_add_entities(entities)


class AjaxSwitch(CoordinatorEntity[AjaxProtegimCoordinator], SwitchEntity):
    """Ajax switch entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AjaxProtegimCoordinator,
        device_id: str,
        hub_id: str,
        device_type: str,
        channel: int,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._hub_id = hub_id
        self._device_type = device_type
        self._channel = channel
        self._attr_unique_id = f"ajax_cobranded_{device_id}_switch_{channel}"

    @property
    def _device(self) -> Any | None:
        return self.coordinator.devices.get(self._device_id)

    @property
    def name(self) -> str:
        device = self._device
        base = device.name if device else "Switch"
        total_channels = SWITCH_DEVICE_TYPES.get(self._device_type, 1)
        if total_channels > 1:
            return f"{base} Channel {self._channel}"
        return base

    @property
    def available(self) -> bool:
        device = self._device
        return device is not None and device.is_online

    @property
    def is_on(self) -> bool | None:
        device = self._device
        if device is None:
            return None
        return device.statuses.get(f"switch_ch{self._channel}", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        cmd = DeviceCommand.on(
            hub_id=self._hub_id,
            device_id=self._device_id,
            device_type=self._device_type,
            channels=[self._channel],
        )
        await self.coordinator.devices_api.send_command(cmd)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        cmd = DeviceCommand.off(
            hub_id=self._hub_id,
            device_id=self._device_id,
            device_type=self._device_type,
            channels=[self._channel],
        )
        await self.coordinator.devices_api.send_command(cmd)
        await self.coordinator.async_request_refresh()
```

- [ ] **Step 5: Implement light.py**

```python
"""Light entities for Ajax Security."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ajax_cobranded.api.models import DeviceCommand
from custom_components.ajax_cobranded.const import DOMAIN
from custom_components.ajax_cobranded.coordinator import AjaxProtegimCoordinator

_LOGGER = logging.getLogger(__name__)

LIGHT_DEVICE_TYPES = {"light_switch_dimmer"}


async def async_setup_entry(
    hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up lights."""
    coordinator: AjaxProtegimCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AjaxLight] = []
    for device_id, device in coordinator.devices.items():
        if device.device_type in LIGHT_DEVICE_TYPES:
            entities.append(
                AjaxLight(
                    coordinator=coordinator,
                    device_id=device_id,
                    hub_id=device.hub_id,
                    device_type=device.device_type,
                    channel=1,
                )
            )

    async_add_entities(entities)


class AjaxLight(CoordinatorEntity[AjaxProtegimCoordinator], LightEntity):
    """Ajax light (dimmer) entity."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: AjaxProtegimCoordinator,
        device_id: str,
        hub_id: str,
        device_type: str,
        channel: int,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._hub_id = hub_id
        self._device_type = device_type
        self._channel = channel
        self._attr_unique_id = f"ajax_cobranded_{device_id}_light_{channel}"

    @property
    def _device(self) -> Any | None:
        return self.coordinator.devices.get(self._device_id)

    @property
    def name(self) -> str:
        device = self._device
        return device.name if device else "Light"

    @property
    def available(self) -> bool:
        device = self._device
        return device is not None and device.is_online

    @property
    def is_on(self) -> bool | None:
        device = self._device
        if device is None:
            return None
        brightness = device.statuses.get(f"brightness_ch{self._channel}", 0)
        return brightness > 0

    @property
    def brightness(self) -> int | None:
        device = self._device
        if device is None:
            return None
        # Ajax uses 0-100, HA uses 0-255
        pct = device.statuses.get(f"brightness_ch{self._channel}", 0)
        return round(pct * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness_pct = 100
        if ATTR_BRIGHTNESS in kwargs:
            brightness_pct = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)

        cmd = DeviceCommand.brightness(
            hub_id=self._hub_id,
            device_id=self._device_id,
            device_type=self._device_type,
            brightness=brightness_pct,
            channels=[self._channel],
        )
        await self.coordinator.devices_api.send_command(cmd)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        cmd = DeviceCommand.brightness(
            hub_id=self._hub_id,
            device_id=self._device_id,
            device_type=self._device_type,
            brightness=0,
            channels=[self._channel],
        )
        await self.coordinator.devices_api.send_command(cmd)
        await self.coordinator.async_request_refresh()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/unit/test_switch.py tests/unit/test_light.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add custom_components/ajax_cobranded/switch.py \
    custom_components/ajax_cobranded/light.py \
    tests/unit/test_switch.py tests/unit/test_light.py
git commit -m "feat(ha): add switch and light entities with device commands"
```

---

## Task 14: E2E Test Script and Interactive CLI

**Files:**
- Create: `scripts/test_connection.py`
- Create: `tests/e2e/test_real_connection.py`

- [ ] **Step 1: Create the interactive CLI script**

```python
#!/usr/bin/env python3
"""Interactive CLI to test Ajax gRPC connection against the real system.

Usage:
    AJAX_EMAIL=your@email.com AJAX_PASSWORD=yourpass python scripts/test_connection.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.spaces import SpacesApi
from custom_components.ajax_cobranded.api.security import SecurityApi


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
        # Login will be implemented once proto compilation is complete
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
```

- [ ] **Step 2: Create E2E test**

```python
"""End-to-end tests against the real Ajax API.

Requires AJAX_EMAIL and AJAX_PASSWORD environment variables.
"""

from __future__ import annotations

import os

import pytest

from custom_components.ajax_cobranded.api.client import AjaxGrpcClient
from custom_components.ajax_cobranded.api.spaces import SpacesApi

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("AJAX_EMAIL") or not os.environ.get("AJAX_PASSWORD"),
        reason="AJAX_EMAIL and AJAX_PASSWORD not set",
    ),
]


class TestRealConnection:
    @pytest.fixture
    async def client(self) -> AjaxGrpcClient:
        c = AjaxGrpcClient(
            email=os.environ["AJAX_EMAIL"],
            password=os.environ["AJAX_PASSWORD"],
        )
        await c.connect()
        yield c
        await c.close()

    @pytest.mark.asyncio
    async def test_connect_and_list_spaces(self, client: AjaxGrpcClient) -> None:
        """Verify we can connect and list spaces."""
        spaces_api = SpacesApi(client)
        spaces = await spaces_api.list_spaces()
        # Should have at least one space
        assert len(spaces) > 0
        for space in spaces:
            assert space.id
            assert space.name
```

- [ ] **Step 3: Make script executable**

```bash
chmod +x scripts/test_connection.py
```

- [ ] **Step 4: Commit**

```bash
git add scripts/test_connection.py tests/e2e/test_real_connection.py
git commit -m "feat: add interactive CLI and E2E test for real Ajax connection"
```

---

## Task 15: Documentation and HACS Distribution

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `CONTRIBUTING.md`
- Create: `hacs.json`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create hacs.json**

```json
{
    "name": "Ajax Security",
    "render_readme": true,
    "homeassistant": "2024.1.0"
}
```

- [ ] **Step 2: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-11

### Added
- Initial release
- gRPC client emulating the Protegim mobile app
- Alarm control panel entity (arm/disarm/night mode)
- Binary sensors (door, motion, smoke, leak, tamper, CO, heat)
- Diagnostic sensors (battery, temperature, humidity, CO2, signal)
- Switch entities (relay, wall switch, socket)
- Light entities (dimmer with brightness)
- Config flow with 2FA support
- Translations: English, Spanish, Catalan
```

- [ ] **Step 3: Create README.md**

```markdown
# Ajax Security for Home Assistant

A Home Assistant custom integration for **Ajax Security Systems** — specifically designed for [Protegim](https://protegim.cat/) users, but works with any Ajax co-branded app.

Communicates via **gRPC** (the same protocol the official mobile app uses). No Enterprise API key required — just your regular account credentials.

## Features

- **Alarm Control Panel**: Arm, disarm, night mode, group arming
- **Binary Sensors**: Door, motion, smoke, leak, tamper, CO, heat
- **Sensors**: Battery level, temperature, humidity, CO2, signal strength
- **Switches**: Relays, wall switches, sockets (multi-channel support)
- **Lights**: Dimmers with brightness control
- **Real-time updates** via gRPC server-streaming
- **2FA support** (TOTP)

## Requirements

- Home Assistant 2024.1.0 or later
- An Ajax Systems / Protegim account (email + password)
- At least one Ajax hub online

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Ajax Security" and install
3. Restart Home Assistant
4. Go to Settings → Integrations → Add Integration → "Ajax Security"

### Manual

1. Copy `custom_components/ajax_cobranded/` to your HA `custom_components/` directory
2. Run `make proto` to compile protobuf files (requires `grpcio-tools`)
3. Restart Home Assistant
4. Add the integration via the UI

## Configuration

1. Enter your Ajax/Protegim email and password
2. If 2FA is enabled, enter your TOTP code
3. Select which spaces (hubs) to add
4. Done!

## Supported Devices

| Type | Devices |
|---|---|
| Door Sensors | DoorProtect, DoorProtectPlus, DoorProtectFibra |
| Motion Sensors | MotionProtect, MotionCam, CombiProtect |
| Fire/Smoke | FireProtect, FireProtect2, FireProtectPlus |
| Water Leak | LeaksProtect |
| Relays/Switches | Relay, WallSwitch, Socket, LightSwitch |
| Lights | LightSwitchDimmer |
| Keypads | Keypad, KeypadPlus, KeypadTouchscreen |
| Sirens | HomeSiren, StreetSiren |

## Troubleshooting

| Problem | Solution |
|---|---|
| "Invalid credentials" | Verify email/password work in the Protegim app |
| "Cannot connect" | Check internet connection, Ajax servers may be down |
| Hub shows offline | Verify hub has internet in the Protegim app |
| 2FA code rejected | Ensure your device clock is synchronized |

## Roadmap

- [ ] Camera/video stream support (VideoEdge, RTSP)
- [ ] Smart lock support (LockBridge)
- [ ] Automation scenarios
- [ ] Push notifications via Firebase
- [ ] LifeQuality sensor full support

## License

MIT
```

- [ ] **Step 4: Create CONTRIBUTING.md**

```markdown
# Contributing

## Development Setup

Everything runs in Docker. No local dependencies needed.

```bash
git clone https://github.com/YOUR_USERNAME/ajax-cobranded-hass.git
cd ajax-cobranded-hass

# Build dev container
make build-docker

# Compile protobuf files
make proto

# Run all checks
make check
```

## Commands

| Command | Description |
|---|---|
| `make check` | Run all checks (lint, format, typecheck, tests, dead code) |
| `make test` | Run unit tests with coverage |
| `make test-e2e` | Run E2E tests (requires AJAX_EMAIL + AJAX_PASSWORD) |
| `make lint` | Run linter |
| `make format` | Format code |
| `make typecheck` | Run type checker |
| `make proto` | Compile protobuf files |
| `make cli` | Interactive connection test |

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(scope):` — New feature
- `fix(scope):` — Bug fix
- `docs:` — Documentation
- `chore:` — Maintenance
- `refactor:` — Code refactoring
- `test:` — Tests

## Adding a New Device Type

1. Find the device's `ObjectType` variant in the proto files
2. Add the mapping to `_DEVICE_TYPE_SENSORS` in `binary_sensor.py`
3. If it has switch/relay capabilities, add to `SWITCH_DEVICE_TYPES` in `switch.py`
4. Write tests for the new mappings
5. Update `README.md` device table

## E2E Testing

```bash
AJAX_EMAIL=your@email.com AJAX_PASSWORD=yourpass make test-e2e
```

Destructive tests (arm/disarm) are skipped by default. To run them:

```bash
AJAX_EMAIL=... AJAX_PASSWORD=... pytest tests/e2e/ -v -m "e2e"
```
```

- [ ] **Step 5: Create CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Build dev container
        run: docker build -f Dockerfile.dev --build-arg PYTHON_VERSION=${{ matrix.python-version }} -t ajax-protegim-dev .

      - name: Run checks
        run: docker run --rm ajax-protegim-dev make check
```

- [ ] **Step 6: Commit**

```bash
git add README.md CHANGELOG.md CONTRIBUTING.md hacs.json .github/
git commit -m "docs: add README, CHANGELOG, CONTRIBUTING, HACS config, and CI workflow"
```

---

## Post-Implementation Notes

### Proto Import Paths

The exact import paths for generated proto stubs (`from custom_components.ajax_cobranded.proto import ...`) will depend on how `compile_protos.sh` flattens or preserves the proto directory structure. After Task 3 completes, you may need to adjust imports in Tasks 7 and 8. The logic and proto field names are correct — only the Python import paths may change.

### Login Implementation

Tasks 5-6 build the session and client infrastructure. The actual gRPC login call (constructing the proto request and calling `LoginByPasswordService/execute`) requires compiled proto stubs. Once Task 3 is complete, add the login implementation to `client.py` using the session's `get_login_params()` method.

### Device Streaming

The coordinator in Task 10 starts with polling. After the basic integration works end-to-end, add gRPC server-streaming via `StreamLightDevicesService` for real-time updates. This is a natural follow-up enhancement.
