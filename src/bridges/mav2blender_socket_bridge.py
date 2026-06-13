import math
import socket
import struct
import time

from pymavlink import mavutil

from config import BASE_DIR, BLENDER_HOST, MAVLINK_BRIDGE_PORT, TELEMETRY_PORT


def set_interval(master, message_id, frequency_hz):
    rate_ms = int(1e6 / frequency_hz)
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
        0,
        message_id,
        rate_ms,
        0,
        0,
        0,
        0,
        0,
    )


master = mavutil.mavlink_connection(MAVLINK_BRIDGE_PORT)
master.wait_heartbeat()
print("[Bridge] Heartbeat OK")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

set_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
set_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_AHRS2, 20)
print("[Bridge] Message intervals set")

x = y = z = roll = pitch = yaw = 0.0
last_send = 0.0
send_interval = 1.0 / 20

try:
    while True:
        msg = master.recv_match(
            type=["LOCAL_POSITION_NED", "AHRS2"], blocking=True, timeout=1.0
        )
        if msg is None:
            continue

        if msg._type == "LOCAL_POSITION_NED":
            x, y, z = msg.x, msg.y, -msg.z
            print("NED\n", msg)

        elif msg._type == "AHRS2":
            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = math.degrees(msg.yaw)
            print("AHRS\n", msg)

        now = time.monotonic()
        if now - last_send >= send_interval:
            sock.sendto(
                struct.pack(
                    "!" + "d" * 6,
                    roll,
                    pitch,
                    yaw,
                    x,
                    y,
                    z,
                ),
                (BLENDER_HOST, TELEMETRY_PORT),
            )
except KeyboardInterrupt:
    if "master" in locals():
        master.close()
        print("[Bridge] Closed.")
