# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Security events now include source device info: `device_name`, `device_id`, `device_type`, and `room_name` — enables automations to identify which device triggered an event

## [0.8.4] - 2026-04-18

### Added
- 2FA (TOTP) authentication: config flow now sends the TOTP code to the Ajax API via `LoginByTotpService` — accounts with two-factor authentication enabled can now complete setup (#7)

### Fixed
- Compiled `login_by_totp` proto stubs added to the repository

## [0.8.3] - 2026-04-17

### Fixed
- Entity naming: add `translations/en.json` so HA resolves `translation_key` at runtime — fixes sensors showing device name with `_2`, `_3` suffixes instead of semantic names (#13)
- Push event routing: events now matched to correct space by hub_id instead of broadcasting to all spaces (#8)
- Photo concurrency: photo URLs now correlated to the requesting device instead of resolving all pending captures (#9)
- Photo cleanup task: properly unregistered on integration reload to prevent duplicate tasks (#10)
- Reconfigure: `unique_id` now updates when email changes (#11)
- Device hierarchy: normalized `via_device` to use `hub_id` consistently across switch, light, sensor, and binary_sensor platforms (#12)

## [0.8.2] - 2026-04-17

### Fixed
- Prevent account lockout: authentication errors (wrong password, locked account) now back off to 30-minute retry interval instead of retrying every poll cycle
- Log clear error message with instructions to reconfigure when auth fails

### Added
- "Already in progress" abort message translated in 14 languages
- "Reconfigure successful" abort message translated in 14 languages

## [0.8.1] - 2026-04-17

### Added
- **Reconfigure flow**: change email, password, or app label without removing the integration (Settings → Devices & Services → Ajax → Reconfigure)
- Translations for reconfigure step in 14 languages

## [0.8.0] - 2026-04-17

### Added
- Hub network sensors via HTS protocol (related to #2, #3, #5):
  - `binary_sensor: Ethernet` — hub ethernet link status
  - `binary_sensor: Mains power` — hub external power supply
  - `sensor: Connection type` — primary active connection (ethernet/wifi/gsm/none)
  - `sensor: Ethernet IP address` — hub ethernet IP
  - `sensor: Ethernet gateway` — hub ethernet default gateway
  - `sensor: Ethernet DNS` — hub ethernet DNS server
  - `sensor: Cellular signal` — cellular signal level (weak/normal/strong)
  - `sensor: Cellular network` — cellular network type (2g/3g/4g)
- HTS binary protocol client for real-time hub-level data not available via gRPC
- Translations for all new sensors in 14 languages (ca, cs, de, es, fr, it, nl, pl, pt, pt-BR, ro, tr, uk)
- `pycryptodome` dependency for protocol encryption
- GitHub Actions release workflow for automated pre-release/release creation on tags
- CI now runs on feature branches (`feat/**`)

### Notes
- HTS runs alongside gRPC — if unavailable, only the new network sensors show as unavailable (graceful degradation)
- No additional configuration required — reuses existing account credentials
- Only one HTS connection per account is allowed by the server (shared with the mobile app session)

## [0.7.0] - 2026-04-16

### Changed (BREAKING)
- Renamed `gsm_type` sensor to `mobile_network_type` — entity IDs will change (e.g., `sensor.*_gsm_type` → `sensor.*_mobile_network_type`)
- Renamed `signal_level` sensor to `signal_strength` — entity IDs will change
- Signal strength sensor now shows text (Strong/Normal/Weak/No signal) instead of numeric values
- SIM status sensor now shows text (OK/Missing/Malfunction/Locked) instead of numeric values

### Fixed
- Issues #4, #5, #6: sensor names are now clear and descriptive

## [0.6.6] - 2026-04-16

### Fixed
- Optimistic state now survives stale server responses for 10 seconds — prevents UI flickering/reverting after arm/disarm when the server hasn't propagated the state change yet (issue #1)
- Used `dataclasses.replace()` for safer Space state updates

## [0.6.5] - 2026-04-15

### Fixed
- Optimistic state update after arm/disarm commands prevents UI from flickering or reverting to stale state
- Timestamp overlay on captured photos now works correctly (RGBA alpha compositing)
- GitHub issue templates added for bug reports and feature requests

## [0.6.4] - 2026-04-15

### Fixed
- Integration reload no longer leaves entities unavailable (fetches device snapshot before starting streams)
- Removed verbose debug logging from push notification handler

## [0.6.3] - 2026-04-14

### Fixed
- Disarm retries automatically on `hub_busy` and `another_transition_is_in_progress` (3 attempts with 2s backoff)
- Removed "disarm from triggered state" from roadmap — no separate triggered state exists; disarm works from armed state with retry

## [0.6.2] - 2026-04-14

### Fixed
- Arm/disarm state now updates immediately in HA UI (switched from debounced to immediate refresh)
- `already_in_the_requested_security_state` errors handled gracefully instead of raising exceptions
- Improved error messages for arm/disarm failures (include server error type)

## [0.6.1] - 2026-04-14

### Added
- Media Browser integration: browse captured photos per device via HA Media Browser (Ajax Security Photos)
- Photo gallery with thumbnails, sorted newest first, photo count per device

### Fixed
- Logbook startup error (`async_describe_events` not found) resolved

## [0.6.0] - 2026-04-14

### Added
- **Photo on Demand**: working photo capture with URL retrieval via NotificationLogService media stream
- Photo storage to `/media/ajax_photos/{device}/` with timestamp overlay (date/time burned into image)
- Configurable photo retention: days (1-365, default 30) and max photos per device (0-10000, default 100)
- Photo persistence across HA restarts (last photo saved to disk per device)
- Automatic photo cleanup on startup and every 24 hours
- Photos browsable via HA Media Browser (Local media → ajax_photos)

### Changed
- Device model identifier changed from "Home Assistant" to Android model for better server compatibility
- Camera entity no longer auto-triggers captures — use the button entity for on-demand photos
- Photo capture button only shown on MotionCam PhOD models (not regular MotionCam)
- Notification ID filtering now matches by device ID for correct multi-camera support
- `DELIVERED_WAS_ALREADY_PERFORMED` response treated as success in photo capture

### Fixed
- Security API errors (arm/disarm rejected) now show proper error messages instead of HTTP 500

## [0.5.0] - 2026-04-13

### Added
- Force arm services (`ajax_cobranded.force_arm`, `ajax_cobranded.force_arm_night`) to arm ignoring open sensors
- Event platform for FCM push notification events (alarm, arm/disarm, tamper, panic, fire, flood, motion, and more)
- Logbook integration with human-readable security event descriptions and icons
- Glass break binary sensor for GlassProtect and CombiProtect devices
- Vibration binary sensor for DoorProtect Plus devices
- MDI icons for all entity types (`icons.json`)

### Changed
- Event parsing uses compiled protobuf definitions from the official Ajax app for accurate event identification
- Push notifications now fire HA events in addition to triggering coordinator refresh
- Tamper sensor renamed to "Case tamper" and problem sensor to "Device problem" for clarity
- Photo capture button now only shown on MotionCam PhOD models (not regular MotionCam)

### Fixed
- Security API errors (arm/disarm rejected) now show proper error messages instead of HTTP 500
- CI workflow now uses explicit `permissions: contents: read` (resolved 7 CodeQL alerts)
- Proto files excluded from coverage calculation to prevent false coverage drops

## [0.4.0] - 2026-04-13

### Added
- IMEI sensor for hub cellular modem identifier
- 11 new language translations (Ukrainian, Polish, German, French, Italian, Portuguese, Dutch, Turkish, Romanian, Czech, Brazilian Portuguese) — total 14 languages
- Example automations (21) for alerts, auto-arm, battery monitoring, and more
- Example Lovelace security dashboard (6-section panel)

### Changed
- GSM type sensor now shows text (2G/3G/4G) instead of raw number
- Removed redundant SIM status sensor (already covered by Cellular connected)

### Fixed
- SIM data now fetched on first refresh (entities created at setup)
- SIM sensors no longer use numeric state_class (string values)

### Security
- Automatic migration of legacy plaintext passwords to SHA-256 hash
- Photo URL domain validation prevents SSRF (only `*.ajax.systems` accepted)
- FCM credentials added to diagnostics redaction set
- Email removed from debug log messages
- Narrowed exception catch from BaseException to Exception
- Internal design docs removed from public repository

## [0.3.0] - 2026-04-12

### Added
- Diagnostics platform for troubleshooting (redacts sensitive data)
- Per-device connectivity binary sensor (online/offline)
- Per-device problem binary sensor (malfunctions detected)
- Hub sensors: GSM type, cellular connected, CRA monitoring, lid tamper
- 46 device type mappings (glass, combi, sirens, REX, transmitters, and more)
- Photo on-demand capture button entity for MotionCam devices
- Status parsing for 30+ device status fields
- Motion detection timestamp (`detected_at`) as attribute
- Disclaimer and legal notice in documentation

### Changed
- FCM credentials now provided by user in options flow (not hardcoded)
- Push notifications are optional — integration works without FCM config
- Hub device no longer duplicated (alarm panel shares device with hub sensors)
- Polling interval defaults to 300s (stream handles real-time)

### Fixed
- `via_device` references corrected across all entity platforms
- Security: removed sensitive data from debug logs
- Security: FCM API key no longer in source code

## [0.2.0] - 2026-04-12

### Added
- Real-time device updates via persistent gRPC stream
- Firebase Cloud Messaging (FCM) push notifications
- Device registry support with hub-peripheral hierarchy
- Entity categories and translation-based naming
- runtime_data pattern (modern HA)

### Fixed
- Config flow space selection (SelectSelector)
- Config flow login timeout (30s)
- gRPC proto version compatibility with HA's grpcio 1.78.0

## [0.1.0] - 2026-04-11

### Added
- Initial release
- Alarm control panel (arm/disarm/night mode/group arming with PIN)
- Binary sensors (door, motion, smoke, CO, heat, leak, tamper)
- Diagnostic sensors (battery, temperature, humidity, CO2, signal)
- Switches and lights for relays and dimmers
- Config flow with 2FA, co-branded app label, space selection
- Translations: English, Spanish, Catalan
- gRPC client with retry/backoff, rate limiting, session refresh
