from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


BLENDER_PATH = BASE_DIR / "submodules" / "blender"
SCENE_PATH = BASE_DIR / "data" / "scene.blend"
SCRIPT_PATH = BASE_DIR / "src" / "blender_scripts" / "blender_script.py"

MAVLINK_BRIDGE_PORT = "udp:127.0.0.1:14560"
MAVLINK_CTRL_PORT = "udp:127.0.0.1:14561"

BLENDER_HOST = "127.0.0.1"
TELEMETRY_PORT = 6781
TARGET_PORT = 6782
