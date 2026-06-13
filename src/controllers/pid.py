import math
import time

from pymavlink import mavutil


class PID:
    def __init__(self, k_p, k_i, k_d) -> None:
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.previous_error = 0
        self.integral = 0

    def control(self, current_error, dt):
        self.integral += current_error * dt
        prop_term = self.k_p * current_error
        int_term = self.k_i * self.integral
        der_term = self.k_d * (current_error - self.previous_error) / dt
        self.previous_error = current_error

        return prop_term + int_term + der_term


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


def run_drone_control(connection_string="udp:127.0.0.1:14561"):
    master = mavutil.mavlink_connection(connection_string)
    master.wait_heartbeat()
    print("Heartbeat done")

    set_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
    print("Requested first msg successfully")

    tstart = time.time()
    very_start_time = time.time()
    current_time = time.time()
    last_time = current_time

    data_array = []

    msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
    target = -msg.z + 10

    pid_controller = PID(0.5, 0, 1)

    time.sleep(0.1)

    try:
        while True:
            current_time = time.time()
            msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)

            x, y, z = msg.x, msg.y, -msg.z
            error = target - z

            dt = current_time - last_time
            pid_error = pid_controller.control(error, dt)
            pid_normalized = max(min(pid_error, 1), -1)
            throttle = int(pid_normalized * 500 + 1500)

            print(f"Error: {error}\nCurrent PID: {pid_error}\n\nPWM: {throttle}")
            data_array.append(z)

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

            last_time = current_time

            if time.time() - tstart > 0.1:
                set_interval(
                    master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 30
                )
                tstart = time.time()

            # Exit after 15 seconds and save telemetry plot
            if (current_time - very_start_time) >= 15:
                import matplotlib.pyplot as plt

                plt.figure(figsize=(8, 5))
                plt.axhline(y=10, color="r")
                plt.plot(data_array)
                plt.savefig("pid_plot.png")
                print("Plot saved as pid_plot.png")
                break

    except KeyboardInterrupt:
        print("\nLoop interrupted by user.")
    finally:
        if "master" in locals():
            master.close()
            print("MAVLink connection closed.")


if __name__ == "__main__":
    run_drone_control("udp:127.0.0.1:14561")
