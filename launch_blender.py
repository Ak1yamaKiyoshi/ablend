
import subprocess
from config import blender_path, scene_path, script_path
import os 

proc = subprocess.run([blender_path, scene_path, "--python", script_path, "-w", "-p", "0", "0", "1280", "720"])


