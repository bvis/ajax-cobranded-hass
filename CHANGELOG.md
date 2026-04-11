# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
