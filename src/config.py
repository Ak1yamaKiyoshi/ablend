from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(__file__).resolve().parent.parent

blender_path = BASE_DIR / "submodules" / "blender"
script_path = BASE_DIR / "src" / "blender_scripts" / "blender_script.py"
scene_path = BASE_DIR / "data" / "scene.blend"

ardupilot_path = BASE_DIR / "submodules" / "ardupilot"

ardupilot_sitl_path = ardupilot_path / "Tools" / "autotest" / "sim_vehicle.py"
