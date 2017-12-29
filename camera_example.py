from valerian import *

new_data = Signal(8, type="in") # 8 bit RGB data coming from the camera
new_line = Signal(1, type="in")  # New line trigger coming from camera
new_frame = Signal(1, type="in") # New frame trigger coming from camera
new_pixel = Signal(1, type="in") # New pixel trigger coming from camera

camera_x = Signal(4) # Derived from new_frame, new_line
camera_y = Signal(4) # Derived from new_line, new_pixel

request_x = Signal(4)
request_y = Signal(4)
response = Signal(8, type="out")

request_x.drive(430)
request_y.drive(200)


def camera_pos(current, increment, clear):
	if bool(clear):
		return 0
	elif int(increment) == 1:
		return int(current) + 1
	else:
		return int(current)


camera_x.drive(camera_pos, args=(camera_x, new_pixel, new_line))
camera_y.drive(camera_pos, args=(camera_y, new_line, new_frame))


data = [False]
def latch(request_x, request_y, camera_x, camera_y, current_data):
	if bool(data[0]):
		return 1
	if int(request_x) == int(camera_x) and int(request_y) == int(camera_y):
		return int(current_data)


response.drive(latch, args=(request_x, request_y, camera_x, camera_y, new_data))

response.io("p11")
new_data.io(["p"+str(x) for x in range(8)])
new_pixel.io("p8")
new_line.io("p9")
new_frame.io("p10")
print(generate_vhdl(globals(), response))
print("")
print(generate_ucf(50, response))