import socket 
import time 
import math 
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# roll, pitch, yaw, x, y, z


i = 0 
while True:
  i += 1 
  time.sleep(1/30)

  x, y, z = 0.0, 0.0, math.cos(i/20) + 1
  roll, pitch, yaw = math.sin(i/10)*20, 0.0, 0.0
  print(z)
  
  sock.sendto(struct.pack("!dddddd", roll, pitch, yaw, x, y, z), ("0.0.0.0", 6781))




  

