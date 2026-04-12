# Ajax Security for Home Assistant

> **Disclaimer**: This is an **unofficial** third-party integration and is not affiliated with, endorsed by, or supported by Ajax Systems. Use at your own risk. This integration communicates with Ajax Systems servers by emulating the official mobile app's protocol. Ajax Systems may change their API at any time, which could break this integration without notice.

A Home Assistant custom integration for **Ajax Security Systems** — works with any co-branded Ajax app.

Communicates via **gRPC** (the same protocol the official mobile app uses). No Enterprise API key required — just your regular account credentials.

## How It Works

Ajax Systems provides co-branded versions of their mobile app to security companies worldwide. Each co-branded app connects to the same Ajax cloud backend but uses a unique **application label** to identify itself. This integration emulates the mobile app's gRPC protocol, so it works with any co-branded variant.

**You need to know the application label of your Ajax provider.** This is an internal identifier that the app sends to the Ajax cloud (see the Known App Labels table below). If you use the main Ajax app, the label is `Ajax`.

## Features

- **Alarm Control Panel**: Arm, disarm, night mode, group arming
- **Binary Sensors**: Door open/close, motion detection, smoke, leak, tamper, CO, heat, CRA monitoring, cellular connection, lid tamper, external contacts, anti-masking, interference detection
- **Sensors**: Battery level, temperature, humidity, CO2, signal strength, GSM type (2G/3G/4G), Wi-Fi signal level
- **Switches**: Relays, wall switches, sockets (multi-channel support)
- **Lights**: Dimmers with brightness control
- **Cameras**: MotionCam photo on-demand capture button
- **Real-time updates**: Persistent gRPC stream for instant sensor state changes
- **Push notifications**: FCM integration for immediate event delivery
- **2FA support** (TOTP)

## Requirements

- Home Assistant 2024.1.0 or later
- An Ajax Security account (email + password)
- At least one Ajax hub online
- The **application label** of your co-branded Ajax app

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) and select **Custom repositories**
3. Add `https://github.com/bvis/ajax-cobranded-hass` with category **Integration**
4. Search for "Ajax Security" in HACS and click **Install**
5. Restart Home Assistant
6. Go to **Settings > Devices & Services > Add Integration** and search for "Ajax Security"

### Manual

1. Download this repository
2. Copy `custom_components/ajax_cobranded/` to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings > Devices & Services > Add Integration** and search for "Ajax Security"

## Configuration

1. Enter your Ajax account **email** and **password**
2. Enter the **App Label** of your co-branded app (see table below, or type your own)
3. If 2FA is enabled, enter your TOTP code
4. Select which spaces (hubs) to add
5. Done

### Known App Labels

Each co-branded Ajax app uses an internal **label name** to identify itself to the Ajax cloud. This label is not always the same as the app's display name. The integration includes all known labels in a dropdown during setup.

| App Label | App Name | Region |
|---|---|---|
| `Ajax` | Ajax Security System | Worldwide |
| `ajax_pro` | Ajax PRO | Worldwide |
| `AIKO` | AIKO | Estonia |
| `3dAlarma` | 3D Alarma | Spain |
| `E-Pro` | E-Pro | — |
| `G4S_SHIELDalarm` | G4S SHIELDalarm | Europe |
| `GSS_Home` | GSSecurity | — |
| `HomeSecure` | HomeSecure | — |
| `Hus_Smart` | Hus Smart | Scandinavia |
| `Novus_alarm` | Novus | — |
| `Protegim_alarma` | Protegim | Spain |
| `Protecta` | Protecta | — |
| `SecureAjax` | SecureAjax | — |
| `Smart_Secure` | Smart & Secure | — |
| `Verux` | Verux | — |
| `Videotech_alarm` | Videotech | — |
| `kale_alarm_x` | Kale Alarm X | Turkey |
| `ADT_Alarm` | ADT Alarm | — |
| `ADT_Secure` | ADT Secure | — |
| `Yoigo_ADT_Alarma` | Yoigo ADT Alarma | Spain |
| `Masmovil_ADT_Alarma` | Másmóvil ADT Alarma | Spain |
| `Euskaltel_ADT_Alarma` | Euskaltel ADT Alarma | Spain |
| `Elotec` | Elotec Ajax | Norway |
| `Yavir` | Yavir | Ukraine |
| `Oryggi` | Oryggi | Iceland |
| `acacio` | acacio | — |

### How to find your app label

If your provider is not in the list above, you can find the correct label by:

1. **Check the app's Google Play URL** — search for the package name (e.g. `com.ajaxsystems.yourapp`) and cross-reference with the table
2. **Inspect network traffic** — the app sends its label in the `application-label` gRPC metadata header on every request
3. **Decompile the APK** — the label is hardcoded in the app's resources as `ajax_app_name` in `strings.xml`

You can type any custom label during setup if yours is not listed.

## Supported Devices

| Type | Devices | Entities |
|---|---|---|
| Hub | Hub, Hub Plus, Hub 2, Hub 2 Plus, Hub 2 4G | Alarm panel, battery, GSM type/connected, CRA monitoring, lid tamper |
| Door Sensors | DoorProtect, DoorProtectPlus, DoorProtectFibra | Door open/close, tamper, battery, temperature, signal, external contacts |
| Motion Sensors | MotionProtect, MotionCam, CombiProtect | Motion detected (real-time), tamper, battery, temperature, signal |
| Fire/Smoke | FireProtect, FireProtect2, FireProtectPlus | Smoke, CO, high temperature, tamper, battery |
| Water Leak | LeaksProtect | Leak detected, tamper, battery |
| Relays/Switches | Relay, WallSwitch, Socket, LightSwitch | On/off per channel |
| Lights | LightSwitchDimmer | Brightness control |
| Cameras | MotionCam (photo on-demand) | Capture photo button |
| Keypads | Keypad, KeypadPlus, KeypadCombi, KeypadTouchscreen | Battery, tamper, temperature, signal, NFC status |
| Sirens | HomeSiren, StreetSiren | Battery, tamper, signal |

## Entity Details

### Hub sensors
- **CRA connection** — binary sensor showing if the hub is connected to the monitoring station
- **Cellular connected** — binary sensor for GSM/4G connection status
- **GSM type** — sensor showing connection type (2G/3G/4G)
- **Lid opened** — tamper detection for the hub enclosure
- **Battery** — hub battery level

### Real-time event sensors
Door open/close and motion detection are **transient events** — they appear when the event occurs and clear automatically. The integration uses a persistent gRPC stream for instant delivery (typically < 1 second latency).

> **Note on motion detection**: Ajax motion sensors (MotionProtect, MotionCam) only report motion events when the system is **armed**. This is a firmware-level behavior — when the system is disarmed, motion detectors are inactive and do not send events. This is by design for battery conservation and to avoid false alarms during normal use.

### Security sensors
- **Anti-masking** — detector obstruction attempt
- **Case drilling** — enclosure drilling attempt
- **Interference** — RF jamming detection
- **External contact** — wired zone status (DoorProtectPlus)

## Troubleshooting

| Problem | Solution |
|---|---|
| "Invalid credentials" | Verify email/password work in your Ajax app |
| "Cannot connect" | Check internet connection; Ajax servers may be down |
| Hub shows offline | Verify hub has internet in your Ajax app |
| 2FA code rejected | Ensure your device clock is synchronized |
| Unexpected errors | Verify your app label matches your co-branded app exactly |
| Motion/door not updating | Check that the gRPC stream is connected (look for "Device stream started" in logs) |

## Roadmap

- [ ] Video stream support (VideoEdge, RTSP)
- [ ] Smart lock support (LockBridge)
- [ ] Photo on-demand image retrieval (capture works, URL retrieval pending)
- [ ] Automation scenarios
- [ ] LifeQuality sensor full support
- [ ] Expand known co-branded app labels
- [ ] SpaceControl (keyfob) support
- [ ] Photo on-demand image retrieval

## Push Notifications (Optional)

For real-time push notifications via Firebase Cloud Messaging (FCM), you need to provide your own FCM credentials. These can be obtained by decompiling your co-branded Ajax app's APK and extracting the Firebase configuration.

The required fields (configured in the integration's Options):
- **FCM Project ID** — Firebase project identifier
- **FCM App ID** — Firebase application ID
- **FCM API Key** — Firebase Web API key
- **FCM Sender ID** — GCM/FCM sender ID

### How to obtain FCM credentials

1. Download your co-branded Ajax app's APK (from APKMirror, APKPure, or similar)
2. Decompile the APK using [jadx](https://github.com/skylot/jadx)
3. Look in `res/values/strings.xml` for `google_app_id`, `gcm_defaultSenderId`, `project_id`
4. The API key may be in `strings.xml` as `google_api_key`, or in a native library (`lib/*/libnative-lib.so` — search for strings starting with `AIza`)

If FCM credentials are not configured, the integration will still work using the persistent gRPC stream for real-time updates. FCM adds an additional push notification channel for faster event delivery.

## Legal Notice

This integration is provided for **personal, non-commercial use** and for **interoperability purposes** as permitted under applicable law (including EU Directive 2009/24/EC on the legal protection of computer programs).

- This project is **not affiliated with Ajax Systems** in any way
- Ajax Systems trademarks and product names belong to their respective owners
- The protobuf definitions included in this integration were derived through reverse engineering of publicly available mobile applications for interoperability purposes
- **No warranty** is provided — this software is provided "as is"
- The authors are not responsible for any damage, data loss, or security issues arising from the use of this integration
- By using this integration, you accept full responsibility for its use with your Ajax security system

## License

MIT
