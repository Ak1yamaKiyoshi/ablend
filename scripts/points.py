import math
import random
import socket
import struct
import time

from pymavlink import mavutil

STATIC_HEIGHT = 10.0
ACCEPTANCE_RADIUS = 0.2


def set_message_interval(master, message_id, frequency_hz):
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


def arm_vehicle(master):
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


conn_str = "udp:127.0.0.1:14561"
master = mavutil.mavlink_connection(conn_str)
master.wait_heartbeat()
print("[Points]: Heartbeat received!")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = ("127.0.0.1", 6782)

set_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 30)
arm_vehicle(master)


class PID:
    def __init__(self, k_p, k_i, k_d) -> None:
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.previous_error = 0
        self.integral = 0

    def control(self, current_error, dt):
        if dt <= 0:
            return 0
        self.integral += current_error * dt
        self.integral = max(min(self.integral, 2), -2)
        prop_term = self.k_p * current_error
        int_term = self.k_i * self.integral
        der_term = self.k_d * (current_error - self.previous_error) / dt
        self.previous_error = current_error
        return prop_term + int_term + der_term


try:
    master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
    time.sleep(5)

    pid_height = PID(0.5, 0.001, 0.5)
    pid_x = PID(0.4, 0.001, 0.3)
    pid_y = PID(0.4, 0.001, 0.3)

    last_time = time.time()
    target_x, target_y, target_height = 0.0, 0.0, STATIC_HEIGHT

    while True:
        msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        x, y, z = msg.x, msg.y, -msg.z

        error_x = target_x - x
        error_y = target_y - y
        error_height = target_height - z

        distance = math.sqrt(error_x**2 + error_y**2 + error_height**2)
        print(distance)
        if distance <= ACCEPTANCE_RADIUS:
            target_x = x + random.uniform(-10.0, 10.0)
            target_y = y + random.uniform(-10.0, 10.0)
            target_height = z + random.uniform(-10.0, 10.0)
            print(
                f"Target resolved, new target: x={target_x} y={target_y} z={target_height}"
            )

        pid_out_height = pid_height.control(error_height, dt)
        pid_out_x = pid_x.control(error_x, dt)
        pid_out_y = pid_y.control(error_y, dt)

        throttle = int(max(min(pid_out_height, 1), -1) * 500 + 1500)
        pitch = int(-max(min(pid_out_x, 1), -1) * 500 + 1500)
        roll = int(max(min(pid_out_y, 1), -1) * 500 + 1500)

        sock.sendto(
            struct.pack("!ddd", target_x, target_y, target_height),
            addr,
        )

        print(
            f"H: Err={error_height:.2f} | X: Err={error_x:.2f} | Y: Err={error_y:.2f}"
        )

        master.mav.rc_channels_override_send(
            master.target_system,
            master.target_component,
            roll,
            pitch,
            throttle,
            1500,
            0,
            0,
            0,
            0,
        )

except KeyboardInterrupt:
    if "master" in locals():
        master.close()
    print("\nMAVLink connection closed.")
