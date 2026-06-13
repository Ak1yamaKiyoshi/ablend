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

    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1,  # 1 - Arm; 0 - Disarm
        0,
        0,
        0,
        0,
        0,
        0,
    )

    print("Armed")


conn_str = "udp:127.0.0.1:14561"
master = mavutil.mavlink_connection(conn_str)
master.wait_heartbeat()
print("Heartbeat done")

set_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
print("Requested first msg successfully")

tstart = time.time()


try:
    x, y, z = 0.0, 0.0, 0.0
    msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
    start_x, start_y, start_z = msg.x, msg.y, msg.z

    target = 10

    while True:
        msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
        x, y, z = msg.x, msg.y, msg.z

        error = target + z
        error_sign = error / abs(error)
        throttle = int(1500 + 50 * error_sign)

        print(error)
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

        if time.time() - tstart > 0.1:
            set_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 30)
            tstart = time.time()

except KeyboardInterrupt:
    if "master" in locals():
        master.close()
        print("MAVLink connection closed.")
