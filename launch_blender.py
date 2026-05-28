
import subprocess
import os 

blender_path = "/home/akiyama/bin/blender-5.1.2-linux-x64/blender"
script_path = os.path.join(os.getcwd(), "blender_script.py")
scene_path = os.path.join(os.getcwd(), "scene.blend")

proc = subprocess.run([blender_path, scene_path, "--python", script_path, "-w", "-p", "0", "0", "1280", "720"])


