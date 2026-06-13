import subprocess

from config import BASE_DIR, BLENDER_PATH, SCENE_PATH, SCRIPT_PATH

proc = subprocess.run(
    [
        str(BLENDER_PATH),
        str(SCENE_PATH),
        "--python",
        str(SCRIPT_PATH),
        "-w",
        "-p",
        "0",
        "0",
        "1920",
        "1200",
    ]
)
