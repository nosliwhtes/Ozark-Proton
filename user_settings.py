#Ozark-Proton default settings (shipped). Applies to every game run with this build.
#Anything already set in the environment or a game's launch options wins over these.
#
#Test mode: add OZARK_TEST=1 to a game's launch options to turn on logging for that game.
#Logs go to ~/ozark-logs/steam-<APPID>.log (used by tools/ozark-smoke.sh).

import os

user_settings = {
    #NVAPI for DLSS/Reflex on NVIDIA (Proton already enables it unless disabled; kept explicit).
    "DXVK_ENABLE_NVAPI": "1",

    #NVIDIA driver shader cache: raise the 1 GB default cap and stop the driver from
    #pruning it, so compiled shaders survive between sessions (fewer stutters on revisits).
    "__GL_SHADER_DISK_CACHE_SIZE": "10737418240",
    "__GL_SHADER_DISK_CACHE_SKIP_CLEANUP": "1",
}

#Test mode also turns on while ~/.config/ozark/test-mode exists (set by tools/ozark-smoke.sh).
if (os.environ.get("OZARK_TEST", "0") not in ("", "0")
        or os.path.exists(os.path.expanduser("~/.config/ozark/test-mode"))):
    user_settings.update({
        "PROTON_LOG": "1",
        "PROTON_LOG_DIR": os.path.expanduser("~/ozark-logs"),
        "DXVK_LOG_LEVEL": "warn",
        "VKD3D_DEBUG": "err",
    })
