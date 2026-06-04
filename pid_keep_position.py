import math
import socket
import struct
import time

from pymavlink import mavutil


def set_message_interval(message_id, frequency_hz):
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


def arm_vehicle():
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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = ("0.0.0.0", 6782)

set_message_interval(mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 30)
arm_vehicle()


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
        prop_term = self.k_p * current_error
        int_term = self.k_i * self.integral
        der_term = self.k_d * (current_error - self.previous_error) / dt
        self.previous_error = current_error

        return prop_term + int_term + der_term


try:
    master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
    time.sleep(1)

    msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)

    target_x = msg.x
    target_y = msg.y
    target_height = -msg.z + 10

    pid_height = PID(0.5, 0.001, 0.8)
    pid_x = PID(0.5, 0.001, 0.8)
    pid_y = PID(0.5, 0.001, 0.8)

    time_counter = time.time()
    last_time = time.time()
    counter = 0

    while True:
        msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        x, y, z = msg.x, msg.y, -msg.z

        error_height = target_height - z
        error_x = target_x - x
        error_y = target_y - y

        pid_out_height = pid_height.control(error_height, dt)
        pid_out_x = pid_x.control(error_x, dt)
        pid_out_y = pid_y.control(error_y, dt)

        norm_height = max(min(pid_out_height, 1), -1)
        norm_x = max(min(pid_out_x, 1), -1)
        norm_y = max(min(pid_out_y, 1), -1)

        throttle = int(norm_height * 500 + 1500)
        pitch = int(-norm_x * 500 + 1500)
        roll = int(norm_y * 500 + 1500)

        sock.sendto(
            struct.pack("!" + "d" * 4, counter, target_x, target_y, target_height), addr
        )

        print(
            f"H: Err={error_height:.2f}, PWM={throttle} | P(X): Err={error_x:.2f}, PWM={pitch} | R(Y): Err={error_y:.2f}, PWM={roll}"
        )

        if (time.time() - time_counter) >= 15:
            time_counter = time.time()
            if counter == 0:
                target_x -= 25
                target_height += 10
                counter += 1
            elif counter == 1:
                target_y -= 25
                target_height -= 10
                counter += 1
            elif counter == 2:
                target_x += 25
                target_height += 10
                counter += 1
            elif counter == 3:
                target_y += 25
                target_height -= 10
                counter = 0

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
