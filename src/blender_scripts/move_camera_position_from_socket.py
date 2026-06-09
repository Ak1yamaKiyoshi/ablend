import bpy
import struct 
import time
import math 
import threading 
import socket 
import queue 


# use cam
scene = bpy.context.scene
cam = bpy.data.objects.get("DroneCamera")

# camera settings
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


def mainloop():
  i = 0 
  while True:
    i += 1
    time.sleep(1/80)
    drone = bpy.data.objects["DroneCamera"]
    drone.location = (math.sin(i/10)*5, math.cos(i/10)*5, 5)
    drone.rotation_euler = (math.sin(i/10)/2, 0.0, 0.0)


def blender_update():
  drone = bpy.data.objects["DroneCamera"]
  try:
    pitch, roll, yaw, x, y, z = telemetry_queue.get_nowait()
    drone.location = (x, y, z)
    drone.rotation_euler = (math.radians(roll), math.radians(pitch), math.radians(yaw))
  except queue.Empty:
    pass
  return 1/80 # time to sleep before next update


def server(q):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind(("0.0.0.0", 6781))

  try:
    while True:
      data,addr = sock.recvfrom(8*6) # 6 * d
      # todo: validate/split to separate commands 
      # pitch, pitch, yaw, x, y, z
      data = struct.unpack("!dddddd", data)
      q.put(data)

  except Exception:
    sock.close()
  except KeyboardInterrupt:
    sock.close()
  finally: sock.close()

telemetry_queue = queue.Queue(maxsize=5)
bpy.app.timers.register(blender_update, ) # blender is not thread-safe, therefore timers needed.


t = threading.Thread(target=server, args=(telemetry_queue,))
t.start()


