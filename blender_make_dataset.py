import bpy
import struct 
import time
import math 
import threading 
import socket 
import queue 


scene = bpy.context.scene
cam = bpy.data.objects.get("Camera")

# camera parameters
cam.data.lens = 20.0 # mm 
cam.data.sensor_fit = 'VERTICAL' 
cam.data.sensor_height = 80 # mm 
scene.render.resolution_x = 720
scene.render.resolution_y = 400
scene.camera = cam

# switch to rendered 
area = [a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'][0]
space = area.spaces.active
space.shading.type = 'RENDERED'
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
space.region_3d.view_perspective = 'CAMERA'

# renderer settings
scene.render.use_motion_blur = False
scene.render.motion_blur_shutter = 0.0   # length of blur; bigger = more

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




def blender_update():
  time.sleep(0.1)
  cam = bpy.data.objects["Camera"]
  car = bpy.data.objects["CAR05-PICKUP"]

  print(f"cam location {cam.location}")
  print(f"car location {car.location}")
  
  return 1/2

def execution_thread():
  pass
  
bpy.app.timers.register(blender_update, )
action_queue = queue.Queue()

t = threading.Thread(target=execution_thread, )
t.start()
