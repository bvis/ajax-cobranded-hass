# P1 Features + icons.json — Design Spec

## Scope

Five features to implement in order:

1. Force Arm Services
2. icons.json
3. Missing Binary Sensors
4. Event Platform
5. Logbook Integration

## 1. Force Arm Services

### Goal

Expose `ignore_alarms=True` to users via custom HA services, so they can arm even when sensors are open.

### Services

- `ajax_cobranded.force_arm` — calls `SecurityApi.arm(space_id, ignore_alarms=True)`
- `ajax_cobranded.force_arm_night` — calls `SecurityApi.arm_night_mode(space_id, ignore_alarms=True)`

### Files

- **`services.yaml`** (new): Service definitions with `target.entity.domain: alarm_control_panel`
- **`__init__.py`**: Register service handlers in `async_setup_entry`, unregister in `async_unload_entry`
- **`strings.json`** + **translations**: Service name/description strings

### Handler logic

1. Receive `service_call` with `entity_id` target
2. Look up the entity's coordinator via `hass.data`
3. Extract `space_id` from coordinator
4. Call `security_api.arm(space_id, ignore_alarms=True)` or `arm_night_mode`
5. Trigger coordinator refresh

## 2. icons.json

### Goal

Better visual consistency with MDI icons per entity type.

### Mapping

```json
{
  "entity": {
    "alarm_control_panel": { "ajax_security": { "default": "mdi:shield-home" } },
    "binary_sensor": {
      "door": { "default": "mdi:door-closed", "state": { "on": "mdi:door-open" } },
      "motion": { "default": "mdi:motion-sensor" },
      "smoke": { "default": "mdi:smoke-detector-variant" },
      "gas": { "default": "mdi:molecule-co" },
      "moisture": { "default": "mdi:water-alert" },
      "tamper": { "default": "mdi:shield-alert" },
      "connectivity": { "default": "mdi:wifi" },
      "problem": { "default": "mdi:alert-circle" },
      "safety": { "default": "mdi:shield-alert" },
      "vibration": { "default": "mdi:vibrate" }
    },
    "sensor": {
      "battery": { "default": "mdi:battery" },
      "temperature": { "default": "mdi:thermometer" },
      "humidity": { "default": "mdi:water-percent" },
      "signal_strength": { "default": "mdi:signal" }
    },
    "switch": { "relay": { "default": "mdi:electric-switch" } },
    "light": { "dimmer": { "default": "mdi:lightbulb-outline" } },
    "button": { "photo_capture": { "default": "mdi:camera" } },
    "camera": { "motion_cam": { "default": "mdi:cctv" } }
  }
}
```

### Files

- **`icons.json`** (new): Icon mapping file

## 3. Missing Binary Sensors

### Goal

Expose glass_break and vibration as dedicated binary sensors instead of mapping to generic tamper.

### Changes to `binary_sensor.py`

Add to `_DEVICE_TYPE_SENSORS`:
- **GlassProtect** (ObjectType 4): add `glass_break` (device_class: `safety`)
- **CombiProtect** (ObjectType 8): add `glass_break` (device_class: `safety`)
- **DoorProtect Plus** (ObjectType 20): add `vibration` (device_class: `vibration`)

### Changes to `devices.py`

Parse status fields for glass_break and vibration from `LightDeviceStatus`. Verify exact field numbers in APK protos.

### Not included

- **steam** (FireProtect 2): alarm event only, not persistent status. Will be handled by Event Platform.
- **tilt**: alarm event only, same reasoning.

## 4. Event Platform (`event.py`)

### Goal

Fire HA events from FCM push notifications so users can build automations on security events (alarms, arm/disarm, door events, etc.).

### Architecture

```
FCM Push → notification.py → parse ENCODED_DATA → decode proto →
  → extract HubEventTag + qualifier → fire hass event →
  → EventEntity records last event → Logbook picks it up
```

### Entity

- One `AjaxSecurityEvent` entity per hub
- Registered event_types: `alarm`, `arm`, `disarm`, `arm_night`, `tamper`, `malfunction`, `door_open`, `door_close`, `motion`, `panic`, `sensor_error`, `connection_lost`, `connection_restored`

### Event data

```python
{
    "event_type": "arm",
    "device_name": "Front Door",
    "device_type": "DoorProtect",
    "user_name": "Basilio",
    "zone": "Living Room",
}
```

### Proto parsing

Decode `ENCODED_DATA` from FCM → `PushNotificationDispatchEvent` proto → extract:
- `notification.hub_event_tag` → maps to event_type
- `notification.device_id` → maps to device_name via coordinator
- `notification.user_id` → maps to user_name
- Unknown tags logged at DEBUG level for future mapping

### Files

- **`event.py`** (new): `AjaxSecurityEvent` entity
- **`notification.py`**: Enhanced parsing to fire events via coordinator
- **`const.py`**: Event type constants, HubEventTag mapping
- **`strings.json`** + **translations**: Event type labels

## 5. Logbook Integration (`logbook.py`)

### Goal

Clean timeline of security events in HA logbook.

### Implementation

- Register event handler via `async_describe_events()` for `ajax_cobranded_event` domain events
- Map event_types to human-readable descriptions:
  - `arm` → "Armed by {user_name}"
  - `disarm` → "Disarmed by {user_name}"
  - `alarm` → "Alarm: {device_name}"
  - `door_open` → "Opened: {device_name}"
  - `motion` → "Motion: {device_name}"
  - etc.
- Icon per event type (shield, door, motion-sensor, etc.)

### Files

- **`logbook.py`** (new): Logbook event descriptions
- **`__init__.py`**: Register logbook platform

## Testing Strategy

Each feature gets unit tests following TDD:
- Force Arm: test service registration, handler calls SecurityApi with ignore_alarms=True
- Binary Sensors: test new ObjectType mappings, status parsing
- Event Platform: test proto parsing, event firing, entity state updates, unknown tag handling
- Logbook: test event description generation

All tests run in Docker. Coverage must stay >80%.

## Dependencies

```
Force Arm → (none)
icons.json → (none)
Binary Sensors → (none, verify protos in APK)
Event Platform → Binary Sensors (shared device type knowledge), APK proto investigation
Logbook → Event Platform (uses same events)
```

## Constraints

- No real devices for Event Platform testing — design from protos, log unknowns
- FCM push notification format must be verified against APK
- All code must pass mypy strict, ruff lint/format, vulture
