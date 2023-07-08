from .registration_2 import register
import settings


def _load_default_setup_settings():
    return settings.DEFAULT_CONFIG.copy()


register(
    id="static_setup",
    entry_point="setups:StaticSetup",
    kwargs=_load_default_setup_settings(),
)
