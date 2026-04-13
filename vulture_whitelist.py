# Vulture whitelist — parameters required by external interfaces but not used by our code
width  # noqa
height  # noqa
obj  # noqa — firebase_messaging callback signature
call  # noqa — ServiceCall parameter in service handlers
disarm_from_night_mode  # noqa — API method kept for future use (server rejects it currently)
