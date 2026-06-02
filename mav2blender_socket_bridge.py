import math
import socket
import struct
import time

from pymavlink import mavutil


def set_interval(message_id, frequency_hz):
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


conn_str = "127.0.0.1:14560"
master = mavutil.mavlink_connection(conn_str)
master.wait_heartbeat()
print("Heartbeat done")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = ("0.0.0.0", 6781)

set_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
set_interval(mavutil.mavlink.MAVLINK_MSG_ID_AHRS2, 20)
print("Requested first msg successfully")

tstart = time.time()


try:
    x, y, z, roll_rad, pitch_rad, yaw_rad = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    while True:
        msg = master.recv_match(type=["LOCAL_POSITION_NED", "AHRS2"], blocking=True)
        if msg._type == "LOCAL_POSITION_NED":
            x, y, z = msg.x, msg.y, msg.z
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
            print("NED\n", msg)

        if msg._type == "AHRS2":
            roll_rad, pitch_rad, yaw_rad = msg.roll, msg.pitch, msg.yaw
            print("AHRS\n", msg)

        if time.time() - tstart > 0.1:
            set_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 30)
            set_interval(mavutil.mavlink.MAVLINK_MSG_ID_AHRS2, 30)
            tstart = time.time()

except KeyboardInterrupt:
    if "master" in locals():
        master.close()
        print("MAVLink connection closed.")
