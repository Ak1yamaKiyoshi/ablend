import math
import queue
import socket
import struct
import threading

import bpy

# use cam
scene = bpy.context.scene
cam = bpy.data.objects.get("DroneCamera")

# camera settings
cam.data.lens = 20.0  # mm
cam.data.sensor_fit = "VERTICAL"
cam.data.sensor_height = 80  # mm
scene.render.resolution_x = 720
scene.render.resolution_y = 400
scene.camera = cam

# switch to rendered
area = [a for a in bpy.context.screen.areas if a.type == "VIEW_3D"][0]
space = area.spaces.active
space.shading.type = "RENDERED"
bpy.context.scene.render.engine = "BLENDER_EEVEE"
space.region_3d.view_perspective = "CAMERA"

# renderer settings
scene.render.use_motion_blur = False
scene.render.motion_blur_shutter = 0.0  # length of blur; bigger = more

# camera zoom
cam.data.show_passepartout = True
cam.data.passepartout_alpha = 1.0
region = next(r for r in area.regions if r.type == "WINDOW")
with bpy.context.temp_override(area=area, region=region):
    bpy.ops.view3d.view_center_camera()

# remove ui
space.show_gizmo = False  # gizmos
space.overlay.show_overlays = False  # grid, axes, names
with bpy.context.temp_override(window=bpy.context.window, area=area):
    bpy.ops.screen.screen_full_area(use_hide_panels=True)


def drone_receiver(q):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 6781))
    while True:
        try:
            data, addr = sock.recvfrom(6 * 8)
            q.put(struct.unpack("!dddddd", data))
        except queue.Empty:
            pass


def point_receiver(q):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 6782))
    while True:
        try:
            data, addr = sock.recvfrom(3 * 8)
            q.put(struct.unpack("!ddd", data))
        except queue.Empty:
            pass


def blender_update():
    drone = bpy.data.objects["Drone"]
    target = {
        0: bpy.data.objects.get("Target"),
    }

    try:
        roll, pitch, yaw, x, y, z = telemetry_queue.get_nowait()
        yaw += 180  # different coordinate system in Ardupilot and Blender
        print(roll, pitch, yaw)

        drone.location = x, y, z
        drone.rotation_euler = (
            math.radians(roll),
            math.radians(pitch),
            math.radians(yaw),
        )
    except:
        pass
    # except queue.Empty:
    #     pass

    try:
        c_x, c_y, c_z = point_queue.get_nowait()
        active_target = target.get(0)
        active_target.location = (c_x, c_y, c_z)

    except:
        pass

    # except queue.Empty:
    #     pass

    return 1 / 80  # time to sleep before next update


telemetry_queue = queue.Queue(maxsize=5)
point_queue = queue.Queue(maxsize=5)
t1 = threading.Thread(target=drone_receiver, args=(telemetry_queue,), daemon=True)
t2 = threading.Thread(target=point_receiver, args=(point_queue,), daemon=True)

bpy.app.timers.register(
    blender_update,
)

t1.start()
t2.start()
