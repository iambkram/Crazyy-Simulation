import os
import sys

_PROFILE = {
    "name": "pc",
    "default_control_type": "PC",
    "force_control_type": True,
    "start_fullscreen": False,
    "resizable": True,
    "use_scaled": True,
}


def configure_pc():
    os.environ["PC_MODE"] = "1"
    os.environ.pop("MOBILE_MODE", None)
    _PROFILE.update({
        "name": "pc",
        "default_control_type": "PC",
        "force_control_type": True,
        "start_fullscreen": False,
        "resizable": True,
        "use_scaled": True,
    })


def configure_mobile():
    os.environ["MOBILE_MODE"] = "1"
    os.environ.pop("PC_MODE", None)
    _PROFILE.update({
        "name": "mobile",
        "default_control_type": "MOBILE",
        "force_control_type": True,
        "start_fullscreen": True,
        "resizable": False,
        "use_scaled": True,
    })


def get_platform():
    if os.environ.get("MOBILE_MODE") == "1":
        _PROFILE.update({
            "name": "mobile",
            "default_control_type": "MOBILE",
            "force_control_type": True,
            "start_fullscreen": True,
            "resizable": False,
            "use_scaled": True,
        })
    elif os.environ.get("PC_MODE") == "1":
        _PROFILE.update({
            "name": "pc",
            "default_control_type": "PC",
            "force_control_type": True,
            "start_fullscreen": False,
            "resizable": True,
            "use_scaled": True,
        })
    return dict(_PROFILE)


def is_mobile():
    if os.environ.get("MOBILE_MODE") == "1":
        return True
    if os.environ.get("PC_MODE") == "1":
        return False
    return _PROFILE["name"] == "mobile"


def is_pc():
    if os.environ.get("PC_MODE") == "1":
        return True
    if os.environ.get("MOBILE_MODE") == "1":
        return False
    return _PROFILE["name"] == "pc"

