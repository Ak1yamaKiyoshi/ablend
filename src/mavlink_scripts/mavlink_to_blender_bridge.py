import math
import time

from pymavlink import mavutil

conn_str = "127.0.0.1:14560"
master = mavutil.mavlink_connection(conn_str)
master.wait_heartbeat()
print("Heartbeat done")


def set_interval(message_id, rate):
    frequency = int(1e6 / rate)
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
        0,
        message_id,
        frequency,
        0,
        0,
        0,
        0,
        0,
    )


set_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
set_interval(mavutil.mavlink.MAVLINK_MSG_ID_AHRS2, 20)
print("Requested the message succesfully")

import socket
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = ("0.0.0.0", 6781)

tstart = time.time()

try:
    x, y, z, roll_rad, pitch_rad, yaw_rad = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    while True:
        msg = master.recv_match(
            type=["LOCAL_POSITION_NED", "AHRS2"], blocking=True
        )  # .to_dict()
        if msg._type == "LOCAL_POSITION_NED":
            x, y, z = msg.x, msg.y, msg.z
            print("xyz", msg)
            sock.sendto(
                struct.pack(
                    "!" + "d" * 6,
                    math.degrees(roll_rad),
                    math.degrees(pitch_rad),
                    -math.degrees(yaw_rad),
                    y,
                    x,
                    -z,
                ),
                addr,
            )

        if msg._type == "AHRS2":
            roll_rad, pitch_rad, yaw_rad = msg.roll, msg.pitch, msg.yaw
            print("ahrs", msg)

        if time.time() - tstart > 0.1:
            set_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 30)
            set_interval(mavutil.mavlink.MAVLINK_MSG_ID_AHRS2, 30)
            tstart = time.time()
except KeyboardInterrupt:
    if "master" in locals():
        master.close()
        print("MAVLink connection closed.")
    pass
