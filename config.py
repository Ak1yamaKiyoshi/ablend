import os

blender_path = "submodules/blender"
script_path = os.path.join(os.getcwd(), "blender_script.py")
scene_path = os.path.join(os.getcwd(), os.path.join("data", "scene.blend"))

ardupilot_path = os.path.join("submodules", "ardupilot")
ardupilot_sitl_path = os.path.join(ardupilot_path, "Tools", "autotest")

# /sim_vehicle.py --map --console
