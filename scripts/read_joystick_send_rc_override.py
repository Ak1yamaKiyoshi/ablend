import struct

import hid
import pymavlink
from pymavlink import mavutil

from src import config

found = None
device = None

for device in hid.enumerate():
    p_string = device.get("product_string", "")
    if p_string and (
        "TX12" in p_string or "Radiomaster" in p_string or "Joystick" in p_string
    ):
        found = True
        break

if not found:
    print("Joystick not found")
    exit()

tx12 = hid.Device(device["vendor_id"], device["product_id"])

m = mavutil.mavlink_connection("udp:127.0.0.1:14561")
print("await heartbeat")
m.wait_heartbeat()

while True:
    data = tx12.read(64)

    btn1, btn2, btn3, x, y, z, rx, ry, rz, s1, s2 = struct.unpack("<BBBHHHHHHHH", data)
    axes = [x, y, z, rx, ry, rz, s1, s2]
    axes_norm = [(val - 1024) / 1024.0 for val in axes]

    m.mav.rc_channels_override_send(
        m.target_system,
        m.target_component,
        int(1500 + axes_norm[1] * -1 * 500),
        int(1500 + axes_norm[0] * 500),
        int(1500 + axes_norm[2] * 500),
        int(1500 + axes_norm[3] * 500),
        0,
        0,
        0,
        0,
    )

    print(f"Axes norm    : {[f'{a:.3f}' for a in axes_norm]}")
