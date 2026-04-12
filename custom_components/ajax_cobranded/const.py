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
CLIENT_DEVICE_MODEL = "Home Assistant"
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
