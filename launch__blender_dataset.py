
import subprocess
from config import blender_path, scene_path, script_path
import os 

proc = subprocess.run([blender_path, "data/scene-v2.blend", "--python", "blender_make_dataset.py", "-w", "-p", "0", "0", "1280", "720"])


