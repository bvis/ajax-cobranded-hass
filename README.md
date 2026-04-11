# Ajax Security for Home Assistant

A Home Assistant custom integration for **Ajax Security Systems** — works with any co-branded Ajax app.

Communicates via **gRPC** (the same protocol the official mobile app uses). No Enterprise API key required — just your regular account credentials.

## How It Works

Ajax Systems provides co-branded versions of their mobile app to security companies worldwide. Each co-branded app connects to the same Ajax cloud backend but uses a unique **application label** to identify itself. This integration emulates the mobile app's gRPC protocol, so it works with any co-branded variant.

**You need to know the application label of your Ajax provider.** This is an internal identifier that the app sends to the Ajax cloud (see the Known App Labels table below). If you use the main Ajax app, the label is `Ajax`.

## Features

- **Alarm Control Panel**: Arm, disarm, night mode, group arming
- **Binary Sensors**: Door, motion, smoke, leak, tamper, CO, heat
- **Sensors**: Battery level, temperature, humidity, CO2, signal strength
- **Switches**: Relays, wall switches, sockets (multi-channel support)
- **Lights**: Dimmers with brightness control
- **Cameras**: MotionCam photo on-demand capture
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

| Type | Devices |
|---|---|
| Door Sensors | DoorProtect, DoorProtectPlus, DoorProtectFibra |
| Motion Sensors | MotionProtect, MotionCam, CombiProtect |
| Fire/Smoke | FireProtect, FireProtect2, FireProtectPlus |
| Water Leak | LeaksProtect |
| Relays/Switches | Relay, WallSwitch, Socket, LightSwitch |
| Lights | LightSwitchDimmer |
| Cameras | MotionCam (photo on-demand) |
| Keypads | Keypad, KeypadPlus, KeypadTouchscreen |
| Sirens | HomeSiren, StreetSiren |

## Troubleshooting

| Problem | Solution |
|---|---|
| "Invalid credentials" | Verify email/password work in your Ajax app |
| "Cannot connect" | Check internet connection; Ajax servers may be down |
| Hub shows offline | Verify hub has internet in your Ajax app |
| 2FA code rejected | Ensure your device clock is synchronized |
| Unexpected errors | Verify your app label matches your co-branded app exactly |

## Roadmap

- [ ] Video stream support (VideoEdge, RTSP)
- [ ] Smart lock support (LockBridge)
- [ ] Automation scenarios
- [ ] Push notifications via Firebase
- [ ] LifeQuality sensor full support
- [ ] Expand known co-branded app labels

## License

MIT
