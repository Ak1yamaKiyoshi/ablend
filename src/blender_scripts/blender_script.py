import math
import queue
import socket
import struct
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import bpy

from config import BASE_DIR, TARGET_PORT, TELEMETRY_PORT

# use cam
scene = bpy.context.scene
cam = bpy.data.objects.get("DroneCamera")

# camera settings
cam.data.lens = 20.0
cam.data.sensor_fit = "VERTICAL"
cam.data.sensor_height = 80
cam.data.show_passepartout = True
cam.data.passepartout_alpha = 1.0

# switch to rendered
scene.render.resolution_x = 720
scene.render.resolution_y = 400
scene.render.use_motion_blur = False
scene.render.motion_blur_shutter = 0.0
scene.render.engine = "BLENDER_EEVEE"
scene.camera = cam

# renderer settings
scene.render.use_motion_blur = False
scene.render.motion_blur_shutter = 0.0  # length of blur; bigger = more

# camera zoom, remove ui
area = next(a for a in bpy.context.screen.areas if a.type == "VIEW_3D")
space = area.spaces.active
region = next(r for r in area.regions if r.type == "WINDOW")
space.shading.type = "RENDERED"
space.show_gizmo = False
space.overlay.show_overlays = False
space.region_3d.view_perspective = "CAMERA"

with bpy.context.temp_override(area=area, region=region):
    bpy.ops.view3d.view_center_camera()

with bpy.context.temp_override(window=bpy.context.window, area=area):
    bpy.ops.screen.screen_full_area(use_hide_panels=True)


def udp_receiver(port, fmt, q):
    size = struct.calcsize(fmt)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    while True:
        try:
            data, addr = sock.recvfrom(size)
            q.put(struct.unpack(fmt, data))
        except Exception as e:
            print(e)


telemetry_queue = queue.Queue(maxsize=2)
target_queue = queue.Queue(maxsize=2)

t1 = threading.Thread(
    target=udp_receiver, args=(TELEMETRY_PORT, "!dddddd", telemetry_queue), daemon=True
)
t2 = threading.Thread(
    target=udp_receiver, args=(TARGET_PORT, "!ddd", target_queue), daemon=True
)


drone = bpy.data.objects["Drone"]
target = bpy.data.objects.get("Target")


def blender_update():
    try:
        roll, pitch, yaw, x, y, z = telemetry_queue.get_nowait()
        # yaw += 180  # ArduPilot → Blender coordinate system
        print(f"[Blender] Roll={roll} Pitch={pitch} Yaw={yaw}")
        print(f"[Blender] x={x} y={y} z={z}")

        drone.location = x, y, z
        drone.rotation_euler = (
            math.radians(roll),
            math.radians(pitch),
            math.radians(yaw),
        )
    except queue.Empty:
        pass
    except Exception as e:
        print(e)

    try:
        cx, cy, cz = target_queue.get_nowait()
        target.location = (cx, cy, cz)
    except queue.Empty:
        pass
    except Exception as e:
        print(e)

    return 1 / 60  # time to sleep before next update


bpy.app.timers.register(
    blender_update,
)

t1.start()
t2.start()
