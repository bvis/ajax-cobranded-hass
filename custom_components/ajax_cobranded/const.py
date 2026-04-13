"""Constants for the Ajax Security integration."""

from enum import IntEnum, StrEnum

DOMAIN = "ajax_cobranded"
MANUFACTURER = "Ajax Systems"

GRPC_HOST = "mobile-gw.prod.ajax.systems"
GRPC_PORT = 443

CLIENT_OS = "Android"
CLIENT_VERSION = "3.30"
APPLICATION_LABEL = "Ajax"  # default (main Ajax app labelName)
KNOWN_APP_LABELS = [
    "Ajax",
    "AIKO",
    "3dAlarma",
    "E-Pro",
    "esahome",
    "G4S_SHIELDalarm",
    "GSS_Home",
    "HomeSecure",
    "Hus_Smart",
    "Novus_alarm",
    "Protegim_alarma",
    "SecureAjax",
    "Smart_Secure",
    "Verux",
    "Videotech_alarm",
    "kale_alarm_x",
    "ADT_Alarm",
    "ADT_Secure",
    "Yoigo_ADT_Alarma",
    "Masmovil_ADT_Alarma",
    "Euskaltel_ADT_Alarma",
    "Elotec",
    "Yavir",
    "Oryggi",
    "acacio",
    "Protecta",
    "ajax_pro",
]
CLIENT_DEVICE_MODEL = "SM-A536B"  # Generic Android model (Samsung Galaxy A53)
CLIENT_DEVICE_TYPE = "MOBILE"
CLIENT_APP_TYPE = "USER"

# Firebase/FCM config keys — credentials provided by user in options flow
CONF_FCM_PROJECT_ID = "fcm_project_id"
CONF_FCM_APP_ID = "fcm_app_id"
CONF_FCM_API_KEY = "fcm_api_key"
CONF_FCM_SENDER_ID = "fcm_sender_id"

SESSION_REFRESH_INTERVAL = 780  # 13 minutes in seconds
STREAM_RECONNECT_MAX_BACKOFF = 60  # seconds
DEFAULT_POLL_INTERVAL = 300  # seconds fallback (stream handles real-time updates)
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


CONF_PHOTO_RETENTION_DAYS = "photo_retention_days"
CONF_PHOTO_MAX_PER_DEVICE = "photo_max_per_device"
DEFAULT_PHOTO_RETENTION_DAYS = 30
DEFAULT_PHOTO_MAX_PER_DEVICE = 100

EVENT_DOMAIN = f"{DOMAIN}_event"

# Map HubEventTag oneof field names to simplified HA event types
HUB_EVENT_TAG_MAP: dict[str, str] = {
    # Arming
    "arm": "arm",
    "arm_attempt": "arm",
    "arm_with_malfunctions": "arm",
    "group_arm": "arm",
    "group_arm_with_malfunctions": "arm",
    # Disarming
    "disarm": "disarm",
    "duress_disarm": "disarm",
    "group_disarm": "disarm",
    # Night mode
    "night_mode_on": "arm_night",
    "night_mode_off": "disarm_night",
    "duress_night_mode_off": "disarm_night",
    # Alarms
    "intrusion_alarm": "alarm",
    "intrusion_alarm_confirmed": "alarm",
    # Tamper
    "tamper_opened": "tamper",
    "front_tamper_opened": "tamper",
    "back_tamper_opened": "tamper",
    # Panic
    "panic_button_pressed": "panic",
    # Battery
    "battery_low": "battery_low",
    # Connection
    "device_communication_loss": "connection_lost",
    "server_connection_loss": "connection_lost",
    "gsm_connection_loss": "connection_lost",
    "ethernet_connection_loss": "connection_lost",
    # Malfunction
    "malfunction": "malfunction",
    # Fire/smoke
    "smoke_detected": "fire",
    # CO
    "high_co_level_detected": "co_alarm",
    # Water
    "leak_detected": "flood",
    # Glass
    "glass_break_detected": "glass_break",
    # Motion
    "motion_detected": "motion",
    # Door
    "door_opened": "door_open",
}

ALL_EVENT_TYPES: list[str] = sorted(set(HUB_EVENT_TAG_MAP.values()))
