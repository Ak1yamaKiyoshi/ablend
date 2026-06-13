import time

from pymavlink import mavutil

from config import MAVLINK_CTRL_PORT


def set_interval(master, message_id, frequency_hz):
    rate_us = int(1e6 / frequency_hz)
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
        0,
        message_id,
        rate_us,
        0,
        0,
        0,
        0,
        0,
    )


def arm(master):
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    print("[Ctrl] Armed")


master = mavutil.mavlink_connection(MAVLINK_CTRL_PORT)
master.wait_heartbeat()
print("[Ctrl] Heartbeat OK")

set_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
arm(master)

tstart = time.time()
x, y, z = 0.0, 0.0, 0.0
start_x = start_y = start_z = 0.0
target = 10

try:
    while True:
        msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
        x, y, z = msg.x, msg.y, -msg.z

        error = target + z
        error_sign = error / abs(error)
        throttle = int(1500 + 50 * error_sign)
        print(f"[Ctrl] Error={error}")

        master.mav.rc_channels_override_send(
            master.target_system,
            master.target_component,
            1500,  # roll
            1500,  # pitch
            throttle,  # throttle
            1500,  # yaw
            0,
            0,
            0,
            0,
        )


except KeyboardInterrupt:
    master.close()
    print("MAVLink connection closed.")
