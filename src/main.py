import math
import socket
import struct
import threading
import time

import hid
import pymavlink
from pymavlink import mavutil


def initialize_rc_joystic():
    found = None
    for device in hid.enumerate():
        if "Radiomaster Pocket" in device["product_string"]:
            found = device["vendor_id"], device["product_id"]
            break

    if found:
        rc_joystic = hid.Device(found[0], found[1])
        rc_joystic.nonblocking = False
        return rc_joystic


def read_rc_joystic(rc_joystic):
    data = rc_joystic.read(64)
    btn1, btn2, btn3, x, y, z, rx, ry, rz, s1, s2 = struct.unpack("<BBBHHHHHHHH", data)
    axes = [x, y, z, rx, ry, rz, s1, s2]
    axes_norm = [
        int(round((val - 1024) / 1024.0, 3) * 500 + 1500) for val in axes
    ]  # -1.0 to +1.0
    axes_norm[1] = (axes_norm[1] - 1500)*-1+1500
    

    return axes_norm


def read_rc_joystic_endless_to(rc_joystic, container):
    if rc_joystic is not None:
        while True:
            container[0] = read_rc_joystic(rc_joystic)


def request_mavlink_telemetry_continous(mav_conn, messages_and_hz):
    while True:
        for message, hz in messages_and_hz:
            mav_conn.mav.command_long_send(
                mav_conn.target_system,
                mav_conn.target_component,
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                0,
                message,
                int(1e6 / hz),
                0,
                0,
                0,
                0,
                0,
            )
            time.sleep(1/10)
        time.sleep(0.1)


def read_mavlink_messages(mav_conn, ned_container, attitude_container):
    tstart = time.perf_counter()
    cur_time = time.perf_counter()
    while True:
        cur_time = time.perf_counter()
        if cur_time - tstart >= 0.5:
            mav_conn.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS, 
                mavutil.mavlink.MAV_AUTOPILOT_INVALID, 
                0, 0, 0
            )
            tstart = cur_time


        msg = mav_conn.recv_match(blocking=True, timeout = 0.01)
        if msg is not None:
            msg_type = msg.get_type()
            if msg_type == "LOCAL_POSITION_NED":
                ned_container[0] = msg.x, msg.y, msg.z, msg.vx, msg.vy, msg.vz, time.time()
            if msg_type == "ATTITUDE":
                attitude_container[0] = msg.roll, msg.pitch, msg.yaw, time.time()




def send_position_orientation_to_blender(
    sock, addr, ned_container, attitude_container, hz=30
):
    tstart = time.perf_counter()
    target_dt = 1 / hz
    while True:
        tend = time.perf_counter()
        dt = tend - tstart

        if dt < target_dt:
            time.sleep(target_dt - dt)

        roll, pitch, yaw, _ = attitude_container[0]
        x, y, z, _, _, _, _ = ned_container[0]

        sock.sendto(
            struct.pack(
                "!" + "d" * 6,
                math.degrees(roll),
                math.degrees(pitch) + 90,
                -math.degrees(yaw),
                y,
                x,
                z,
            ),
            addr,
        )
        tstart = time.perf_counter()



if __name__ == "__main__":
    state = {
        "rc_channels": [[1500, 1000, 1500, 1500, 1000, 1000, 1000, 1000]],  # pwm
        "attitude_rpy": [[0.0, 0.0, 0.0, 0.0]], # r, p, y, time   # rad
        "ned_xyz_vxvyvz": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], # r, p, y, time  # m, m/s
    }


    print("Initialize rc")
    rc = initialize_rc_joystic()
    rc_joystic_read_to_thread = threading.Thread(
        target=read_rc_joystic_endless_to, args=(rc, state["rc_channels"]), daemon=True
    )
    rc_joystic_read_to_thread.start()
    print("RC found" if rc is not None else "RC not found")


    print("Initialize Mavlink")
    mavlink_messages_with_hz_to_request = [
        (mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 100),
        (mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 100),
    ]
    conn_str = "127.0.0.1:14560"
    master = mavutil.mavlink_connection(conn_str)
    master.wait_heartbeat()
    request_mavlink_telemetry_continous_thread = threading.Thread(target=request_mavlink_telemetry_continous, args=(master, mavlink_messages_with_hz_to_request))
    request_mavlink_telemetry_continous_thread.start()

    read_mavlink_messages_thread = threading.Thread(
        target=read_mavlink_messages,
        args=(master, state["ned_xyz_vxvyvz"], state["attitude_rpy"]),
        daemon=True,
    )
    read_mavlink_messages_thread.start()
    print("Mavlink initialized")


    print("Initialize udp socket for blender")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = ("0.0.0.0", 6781)
    send_position_orientation_to_blender_thread = threading.Thread(
        target=send_position_orientation_to_blender,
        args=(sock, addr, state["ned_xyz_vxvyvz"], state["attitude_rpy"], 24),
    )
    send_position_orientation_to_blender_thread.start()
    print("Blender udp socket initialized.")


    while True:
        time.sleep(1 / 100)
        print(state["rc_channels"][0], state["attitude_rpy"])

        if state['rc_channels'][0][6] > 1800:
            master.mav.rc_channels_override_send(
                master.target_system, master.target_component, 
                state["rc_channels"][0][0], state["rc_channels"][0][1], state["rc_channels"][0][2], state["rc_channels"][0][3], 0, 0, 0, 0
            )


        
