import math
import random
import socket
import struct
import time

from pymavlink import mavutil

from config import BASE_DIR, BLENDER_HOST, MAVLINK_CTRL_PORT, TARGET_PORT
from src.controllers.pid import PID

STATIC_HEIGHT = 10.0
ACCEPTANCE_RADIUS = 0.2


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


def clamp(val, lo=-1, hi=1):
    return max(lo, min(hi, val))


def to_pwm(normalized):
    return int(normalized * 500 + 1500)


master = mavutil.mavlink_connection(MAVLINK_CTRL_PORT)
master.wait_heartbeat()
print("[Ctrl] Heartbeat OK")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

set_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
arm(master)

master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
time.sleep(1)

target_x = 0.0
target_y = 0.0
target_z = STATIC_HEIGHT

pid_x = PID(0.5, 0.001, 0.8)
pid_y = PID(0.5, 0.001, 0.8)
pid_z = PID(0.5, 0.001, 0.8)

last_time = time.time()

try:
    while True:
        msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
        now = time.time()
        dt = now - last_time
        last_time = now

        x, y, z = msg.x, msg.y, -msg.z

        error_x = target_x - x
        error_y = target_y - y
        error_z = target_z - z

        distance = math.sqrt(error_x**2 + error_y**2 + error_z**2)
        print(f"[Ctrl] Distance={distance}")
        if distance <= ACCEPTANCE_RADIUS:
            target_x = x + random.uniform(-10.0, 10.0)
            target_y = y + random.uniform(-10.0, 10.0)
            target_z = z + random.uniform(-10.0, 10.0)
            print(
                f"[Ctrl] Target resolved, new target: x={target_x} y={target_y} z={target_z}"
            )

        roll = to_pwm(clamp(pid_y.control(target_y - y, dt)))
        pitch = to_pwm(-clamp(pid_x.control(target_x - x, dt)))
        throttle = to_pwm(clamp(pid_z.control(target_z - z, dt)))

        sock.sendto(
            struct.pack("!ddd", target_x, target_y, target_z),
            (BLENDER_HOST, TARGET_PORT),
        )

        print(
            f"[Ctrl] X: Err={error_x:.2f}, PWM={pitch} | Y: Err={error_y:.2f}, PWM={roll} | Z: Err={error_z:.2f}, PWM={throttle}"
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
    master.close()
    print("[Ctrl] MAVLink connection closed.")
