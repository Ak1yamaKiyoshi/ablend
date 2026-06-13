import hid # pip isntall hid 
import struct 

found = None
for device in hid.enumerate():
  if "Radiomaster Pocket" in device['product_string']:
    found = device['vendor_id'], device['product_id']
    break

if not found:
  print("tx12 not found")
  exit()

tx12 = hid.Device(found[0], found[1])
tx12.nonblocking = False

while True:
  data = tx12.read(64)

  btn1, btn2, btn3, x, y, z, rx, ry, rz, s1, s2 = struct.unpack('<BBBHHHHHHHH', data)
  axes = [x, y, z, rx, ry, rz, s1, s2]
  axes_norm = [(val - 1024) / 1024.0 for val in axes]  # -1.0 to +1.0

  print(f"Axes norm    : {[f'{a:.3f}' for a in axes_norm]}")
  print(f"Buttons high : {bin(btn1)[2:].zfill(8)} {bin(btn2)[2:].zfill(8)} {bin(btn3)[2:].zfill(8)}")

