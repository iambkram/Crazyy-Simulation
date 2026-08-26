"""Active edition profile. Entry points call configure_pc() / configure_mobile() before importing the game."""

_PROFILE = {
    "name": "pc",
    "default_control_type": "PC",
    "force_control_type": False,
    "start_fullscreen": False,
    "resizable": True,
    "use_scaled": True,
}


def configure_pc():
    _PROFILE.update({
        "name": "pc",
        "default_control_type": "PC",
        "force_control_type": False,
        "start_fullscreen": False,
        "resizable": True,
        "use_scaled": True,
    })


def configure_mobile():
    _PROFILE.update({
        "name": "mobile",
        "default_control_type": "MOBILE",
        "force_control_type": True,
        "start_fullscreen": True,
        "resizable": False,
        "use_scaled": True,
    })


def get_platform():
    return dict(_PROFILE)


def is_mobile():
    return _PROFILE["name"] == "mobile"


def is_pc():
    return _PROFILE["name"] == "pc"
