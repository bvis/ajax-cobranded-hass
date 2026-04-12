# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-12

### Added
- Real-time device updates via persistent gRPC stream (door open/close, motion, smoke, leak, tamper)
- Firebase Cloud Messaging (FCM) push notifications for instant event delivery
- FCM token registration with Ajax servers via gRPC UpsertPushTokenService
- Device registry support — all entities grouped under their physical device
- Hub device with via_device linking for peripheral devices
- Entity categories: battery and signal as diagnostic entities
- Entity translations for signal level and switch channels
- Signal strength sensor disabled by default (low-value diagnostic)
- runtime_data pattern for typed config entry data

### Changed
- Default poll interval increased to 300s (5 min) — stream handles real-time now
- Entities use translation_key and device_class auto-naming instead of hardcoded names
- Switched from hass.data dict to entry.runtime_data

### Fixed
- Config flow space selection now uses SelectSelector (fixes HA UI serialization error)
- Config flow login timeout (30s) prevents HA from killing the flow
- asyncio.CancelledError properly caught in config flow
- gRPC proto version compatibility with HA's grpcio 1.78.0

## [0.1.0] - 2026-04-11

### Added

#### Alarm Control Panel
- Arm, disarm, and night mode for spaces (hubs)
- Group arming and disarming
- Optional PIN code protection with hashed storage

#### Sensors
- Binary sensors: door, motion, smoke, CO, heat, water leak, tamper
- Diagnostic sensors: battery level, temperature, humidity, CO2, signal strength
- Automatic entity creation based on device type

#### Actuators
- Switches for relays, wall switches, sockets, and multi-channel light switches
- Lights for dimmers with brightness control

#### Camera
- MotionCam photo on-demand capture

#### Configuration
- Config flow with masked password field
- Two-factor authentication (TOTP)
- Configurable co-branded app label (27+ known Ajax partner apps)
- Space (hub) selection
- Options flow for poll interval and PIN code

#### Security
- Passwords stored only as SHA-256 hash, never plaintext
- Session tokens kept in memory only, not persisted to disk
- PIN code stored as SHA-256 hash
- Sanitized error messages — no raw server data in logs
- TLS-only gRPC connection
- Client-side rate limiting

#### Architecture
- gRPC client emulating the official Ajax mobile app protocol
- No Enterprise API key required
- Automatic session refresh
- Retry with exponential backoff
- Graceful degradation when hub goes offline

#### Internationalization
- English, Spanish, and Catalan translations
