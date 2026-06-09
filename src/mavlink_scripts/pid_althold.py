import math 
import time 
from pymavlink import mavutil 
from dataclasses import dataclass
import threading 
import matplotlib.pyplot as plt 
import numpy as np 


m = mavutil.mavlink_connection('udp:127.0.0.1:14561')
m.wait_heartbeat()

m.mav.command_long_send(
  m.target_system, m.target_component,
  mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
  mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
  1e6 / 30,
  0,0, 0,0,0
)

m.mav.rc_channels_override_send(
  m.target_system, m.target_component, 
  1500, 1500, 1000, 1500, 0, 0, 0, 0
)

time.sleep(0.1)

m.mav.command_long_send(
  m.target_system, m.target_component,
  mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
  0, 
  1.0,
  0.0, 0.0, 0.0, 0.0, 0.0, 0.0
)

time.sleep(0.5)


@dataclass(slots=True)
class PIDData:
  p: float 
  i: float 
  d: float 
  previous_error: float 

@dataclass(slots=True)
class PIDConfig:
  kp: float 
  ki: float 
  kd: float 


def update(error:float, dt:float, values:PIDData, config:PIDConfig):
  values.p = error * config.kp 
  values.i = ((error + error) * dt) * config.ki
  values.d = (error - values.previous_error) * config.kd
  values.previous_error = error
  out = values.p + values.i + values.d
  return out, values, config


pid_data = PIDData(0.0, 0.0, 0.0, 0.0)
pid_config = PIDConfig(0.65, 0.1, 10.5)


def request():
  global m
  while True:
    m.mav.command_long_send(
      m.target_system, m.target_component,
      mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
      mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
      1e6 / 30,
      0,0, 0,0,0
    )
    time.sleep(1)

thread_request = threading.Thread(target=request, daemon=True)
thread_request.start()


target_alt = 30 
x, y, z = 0.0, 0.0, 0.0

log = []# [z, target, out, cmd, p, i, d]

tstart = time.time()

while 1:
  msg = m.recv_match(type=["LOCAL_POSITION_NED"], blocking=True)
  current_alt = -msg.z
  error = target_alt - current_alt

  out, pid_data, pid_config = update(error, 1/50, pid_data, pid_config)
  out = max(min(out, 1.0), -1)
  throttle_control_command = int(500 * out + 1500)
  
  print(f"alt err: {error:7.1f}, out: {out:5.2f}, cmd throttle: {throttle_control_command:04d}")

  time.sleep(1/50)
  
  m.mav.rc_channels_override_send(
    m.target_system, m.target_component, 
    1500, 1500, throttle_control_command, 1500, 0, 0, 0, 0
  )
  log.append([current_alt, target_alt, out, throttle_control_command, pid_data.p, pid_data.i, pid_data.d])

  if time.time() - tstart > 10:
    break


log_array = np.array(log)
plt.title(f"kp: {pid_config.kp:3.2f}, ki: {pid_config.ki:3.2f}, kd: {pid_config.kd:3.2f}")
plt.plot(log_array[:, 0], label='current_alt')
plt.plot(log_array[:, 1], label='target_alt')
plt.legend()
plt.savefig('althold_log.png')


#  error = target - current_alt
#  error_sign = error / abs(error)
#  throttle = int(1500 + 100 * error_sign)
#  print(throttle, error)



