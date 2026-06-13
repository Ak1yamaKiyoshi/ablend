"""
MAVLink timing diagnostic - 20 seconds
Measures: recv_match wait time, rc_override send time, full loop time
"""

import statistics
import time

from pymavlink import mavutil

from config import MAVLINK_CTRL_PORT


def set_interval(master, message_id, frequency_hz):
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
        0,
        message_id,
        int(1e6 / frequency_hz),
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


master = mavutil.mavlink_connection(MAVLINK_CTRL_PORT)
master.wait_heartbeat()
print("[Diag] Heartbeat OK")

set_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 20)
arm(master)

# Warm up - discard first message
master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
time.sleep(1)

# --- Measurement buckets ---
recv_times = []  # time blocked in recv_match
send_times = []  # time to send rc_override
loop_times = []  # full iteration time

print("[Diag] Starting 20s measurement...\n")
deadline = time.time() + 20
loop_start = time.time()

try:
    while time.time() < deadline:
        loop_t0 = time.time()

        # --- recv_match ---
        recv_t0 = time.time()
        msg = master.recv_match(type=["LOCAL_POSITION_NED"], blocking=True, timeout=2.0)
        recv_dt = time.time() - recv_t0

        if msg is None:
            print("[Diag] WARN: recv_match timed out (2s)")
            continue

        recv_times.append(recv_dt)

        # --- rc_override send ---
        send_t0 = time.time()
        master.mav.rc_channels_override_send(
            master.target_system,
            master.target_component,
            1500,
            1500,
            1500,
            1500,
            0,
            0,
            0,
            0,
        )
        send_dt = time.time() - send_t0
        send_times.append(send_dt)

        loop_dt = time.time() - loop_t0
        loop_times.append(loop_dt)

        print(
            f"recv={recv_dt * 1000:6.2f}ms  "
            f"send={send_dt * 1000:6.2f}ms  "
            f"loop={loop_dt * 1000:6.2f}ms"
        )

except KeyboardInterrupt:
    print("\n[Diag] Interrupted early")
finally:
    master.close()


# --- Report ---
def report(label, data):
    if not data:
        print(f"{label}: no data")
        return
    print(f"\n{label} ({len(data)} samples):")
    print(f"  mean   : {statistics.mean(data) * 1000:.2f} ms")
    print(f"  median : {statistics.median(data) * 1000:.2f} ms")
    print(f"  stdev  : {statistics.stdev(data) * 1000:.2f} ms")
    print(f"  min    : {min(data) * 1000:.2f} ms")
    print(f"  max    : {max(data) * 1000:.2f} ms")

    # Spikes > 3x median
    med = statistics.median(data)
    spikes = [x for x in data if x > med * 3]
    if spikes:
        print(
            f"  spikes (>3x median): {len(spikes)}x, worst={max(spikes) * 1000:.2f}ms"
        )


print("\n" + "=" * 50)
print(f"Total iterations : {len(loop_times)}")
print(f"Duration         : 20s → expected ~{20 * 20} iters at 20Hz")
report("recv_match", recv_times)
report("rc_override send", send_times)
report("full loop", loop_times)
