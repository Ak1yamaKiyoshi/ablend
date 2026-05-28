import bpy

# use cam
scene = bpy.context.scene
cam = bpy.data.objects.get("DroneCamera")
scene.camera = cam


# switch to rendered 
area = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'][0]
space = area.spaces.active
space.shading.type = 'RENDERED'
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
space.region_3d.view_perspective = 'CAMERA'

# camera zoom 
cam.data.show_passepartout = True
cam.data.passepartout_alpha = 1.0
region = next(r for r in area.regions if r.type == 'WINDOW')
with bpy.context.temp_override(area=area, region=region):
    bpy.ops.view3d.view_center_camera()

# remove ui 
space.show_gizmo = False                # gizmos
space.overlay.show_overlays = False     # grid, axes, names
with bpy.context.temp_override(window=bpy.context.window, area=area):
    bpy.ops.screen.screen_full_area(use_hide_panels=True)


import time
import math 
import threading 

def mainloop():
  # example moving & rotating object 
  i = 0 
  while True:
    i += 1
    time.sleep(1/60)
    drone = bpy.data.objects["Drone"]
    drone.location = (math.sin(i/10)*5, math.cos(i/10)*5, 5)
    drone.rotation_euler = (math.sin(i/10), 0.0, 0.0)   # x, y, z; degrees→radians

t = threading.Thread(target=mainloop)
t.start()

