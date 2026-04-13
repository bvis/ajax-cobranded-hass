# Improvement Plan — Ajax Security HA Integration

Prioritized list of improvements based on analysis of foXaCe/ajax-security-hass, prismagroupsa/Ajax_alarm_ha_integration, HA platinum integration patterns, and real-world testing.

## Priority 1 — High impact, moderate effort

### 1.1 Event Platform (`event.py`)
**Why:** Without events, users can't trigger automations from button presses, doorbell rings, or detection events via the HA automation UI. This is the single biggest feature gap.

**Entities:**
- SpaceControl keyfob: `single_press`, `double_press`, `long_press`, `panic`
- KeyPad: `arm`, `disarm`, `panic`, `emergency`
- Doorbell: `ring`
- MotionCam AI: `motion`, `human`, `vehicle`, `pet` (if VideoEdge available)

**Data source:** FCM push notifications (`ENCODED_DATA` → `PushNotificationDispatchEvent.notification` → `HubEventTag`). Parse the event tag and qualifier from the notification proto to determine event type and source device.

**Implementation:**
1. Add `Platform.EVENT` to PLATFORMS
2. Create `event.py` with `AjaxSecurityEvent` entity per device that supports events
3. In `notification.py`, parse `HubEventTag` from ENCODED_DATA and fire events via `hass.bus.async_fire()`
4. Register event types in entity descriptions

**Effort:** Medium (3-4 hours). Requires parsing the notification proto properly.

### 1.2 Force Arm Services
**Why:** Real-world scenario: you want to arm but a window is open. The app handles this with "ignore problems" — we need the same.

**Implementation:**
1. Register custom services `ajax_cobranded.force_arm` and `ajax_cobranded.force_arm_night` in `services.yaml`
2. These call `SecurityApi.arm(space_id, ignore_alarms=True)` which already exists
3. Register handlers in `__init__.py`

**Effort:** Low (1 hour). The API already supports `ignore_alarms=True`.

### 1.3 Logbook Integration (`logbook.py`)
**Why:** Clean timeline of security events (who armed, when a door opened, which sensor triggered).

**Implementation:**
1. Fire custom HA events from `notification.py` when push notifications arrive: `ajax_armed`, `ajax_disarmed`, `ajax_alarm`, `ajax_door_opened`, etc.
2. Create `logbook.py` with `async_describe_events()` that maps events to human-readable descriptions with icons
3. Parse the user name from the notification to show "Armed by Basilio" etc.

**Effort:** Medium (2-3 hours).

### 1.4 Missing Binary Sensors
**Why:** foXaCe has specific sensors for glass_break, shock, tilt, steam that we map to generic tamper.

**Sensors to add:**
- `glass_break` — GlassProtect devices (currently only tamper)
- `shock` / `vibration` — DoorProtect Plus (accelerometer alarm events)
- `tilt` — DoorProtect Plus (accelerometer tilt detection)
- `steam` — FireProtect 2 (steam detection)

**Data source:** These come as StatusUpdate in the gRPC stream (fields we already parse but don't expose as dedicated entities) or as alarm events via FCM push.

**Effort:** Low (1-2 hours). Mostly mapping new status fields to binary sensor types.

---

## Priority 2 — Medium impact, moderate effort

### 2.1 Lock Platform (`lock.py`)
**Why:** Users with LockBridge (Yale smart lock) expect a lock entity.

**Implementation:**
1. Create `lock.py` with `AjaxLock` entity
2. Parse `smart_lock` status from `LightDeviceStatus` (field 66)
3. Commands via `SwitchSmartLockService` gRPC (proto exists: `switch_smart_lock/`)
4. States: locked, unlocked, locking, unlocking, jammed

**Effort:** Medium (3-4 hours). Need to compile switch_smart_lock protos.

### 2.2 Valve Platform (`valve.py`)
**Why:** WaterStop devices should be controlled as native HA valves, not switches.

**Implementation:**
1. Create `valve.py` with `AjaxWaterStopValve` entity
2. Parse `water_stop_valve_stuck` status
3. Commands need investigation — may be via device command service

**Effort:** Medium (2-3 hours).

### 2.3 Update Platform (`update.py`)
**Why:** Users want to see firmware status and update availability.

**Data source:** `streamHubObject` v2 field 200 (`DeviceFirmwareUpdates`) and field 201 (`SystemFirmwareUpdate`).

**Implementation:**
1. Create `update.py` with `AjaxFirmwareUpdate` entity
2. Parse firmware info from `streamHubObject` response
3. Show current version, latest available, update progress

**Effort:** Medium (3 hours). Need to parse firmware proto fields.

### 2.4 icons.json
**Why:** Better visual consistency with proper MDI icons per entity type.

**Implementation:**
1. Create `icons.json` mapping entity types to MDI icons
2. Door: `mdi:door`, Motion: `mdi:motion-sensor`, Smoke: `mdi:smoke-detector`, etc.

**Effort:** Low (30 minutes).

### 2.5 DHCP Discovery
**Why:** Automatic hub detection on the local network without manual setup.

**Implementation:**
1. Add `dhcp` entries to `manifest.json` with Ajax hub MAC prefixes (`9C:75:6E`, `38:B8:EB`)
2. Implement `async_step_dhcp` in config_flow

**Note:** This only helps if the hub is on the same network as HA. The gRPC connection is still to the cloud.

**Effort:** Low (1 hour).

---

## Priority 3 — Nice to have, higher effort

### 3.1 Number Platform (`number.py`)
**Why:** Expose configurable device settings (shock sensitivity, LED brightness, etc.)

**Entities:**
- DoorProtect Plus: tilt angle threshold (5-25°)
- Socket: current protection limit (1-16A)
- Dimmer: min/max brightness, touch sensitivity

**Data source:** These are device settings, not statuses. Require `UpdateHubDeviceService` gRPC to write.

**Effort:** High (4-5 hours). Need to understand the update device settings flow.

### 3.2 Select Platform (`select.py`)
**Why:** Configuration options that are enum-based (shock sensitivity: low/normal/high, etc.)

**Implementation:** Similar to number platform but with enum options.

**Effort:** High (4-5 hours). Same dependency on UpdateHubDeviceService.

### 3.3 Device Tracker (`device_tracker.py`)
**Why:** Show hub location on HA map.

**Data source:** Hub geoFence coordinates. May be available in the space/facility data.

**Effort:** Low (1-2 hours) if data is available.

### 3.4 Persistent Notification Service
**Why:** Show alarm events as HA persistent notifications with configurable filters.

**Implementation:**
1. Add options flow setting: notification filter (none, alarms only, security, all)
2. From FCM push handler, create `persistent_notification.create` based on filter

**Effort:** Medium (2 hours).

### 3.5 Device Handler Architecture Refactor
**Why:** Current monolithic `_DEVICE_TYPE_SENSORS` dict becomes unwieldy as device types grow. A per-device-type handler pattern (like foXaCe's `devices/` directory) would be cleaner.

**Implementation:**
1. Create `devices/` directory with a base class and per-device-type modules
2. Each handler defines which binary sensors, sensors, switches, events it supports
3. Entity platforms query handlers instead of static dicts

**Effort:** High (6-8 hours). Significant refactor, should be done when adding new entity types.

---

## Known Limitations (Cannot Fix)

These are protocol-level limitations that cannot be resolved by emulating the mobile app:

- **Hub ethernet/WiFi details** (IP, mask, gateway, DNS) — only available via HTS internal channel
- **Hub external power status** — only via HTS
- **Hub tamper (lid) real state** — the `lid_opened` status exists in the proto but the server doesn't send it in `StreamLightDevices` for the hub
- **Photo on-demand URL retrieval** — v2 capture works but the photo URL only arrives via the v3 detection area stream, which returns `permission_denied` for our sessions
- **SpaceControl keyfob listing** — keyfobs don't appear in `StreamLightDevices` (they may appear in a different device list API)
- **Motion detection when disarmed** — Ajax firmware disables motion reporting when the system is disarmed (battery conservation)
- **Shock/vibration as persistent sensor** — these are alarm events, not persistent statuses

## Dependencies and Prerequisites

| Improvement | Depends on |
|---|---|
| Event platform | FCM push notification parsing (notification.py) |
| Force Arm services | Nothing (API already supports it) |
| Logbook | FCM push parsing + event platform |
| Lock platform | switch_smart_lock proto compilation |
| Valve platform | Device command investigation |
| Update platform | streamHubObject firmware field parsing |
| Number/Select | UpdateHubDeviceService proto understanding |
| Device tracker | Space/facility geo data source |

## Estimated Total Effort

| Priority | Items | Effort |
|---|---|---|
| P1 | 4 items | ~8-10 hours |
| P2 | 5 items | ~10-12 hours |
| P3 | 5 items | ~16-20 hours |
| **Total** | **14 items** | **~34-42 hours** |
