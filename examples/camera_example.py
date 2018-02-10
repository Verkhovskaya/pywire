from pywire import *

camera_clock = Signal(1, io="out", port="P40")  # 25MHz
frame_invalid = Signal(1, io="in", port="P26")  # New frame trigger coming from camera. Aka VSYNC
line_valid = Signal(1, io="in", port="P34")  # New line trigger coming from camera. AKA HREF
pixel_clock = Signal(1, io="in", port="P23")  # New pixel trigger coming from camera. AKA PCLK

# 8 bit RGB data coming from the camera
new_data = Signal(8, io="in", port=['P9', 'P11', 'P7', 'P14', 'P5', 'P16', 'P2', 'P21'])

camera_x = Signal(10)  # Derived from new_frame, new_line
camera_y = Signal(10)  # Derived from new_line, new_pixel

request_x = Signal(10).drive(430)
request_y = Signal(10).drive(200)
response = Signal(8, io="out", port=["P134", "P133", "P132", "P131", "P127", "P126", "P124", "P123"])


def halve_frequency(slow_clock):
	if slow_clock == 1:
		return 0
	else:
		return 1


camera_clock.drive(halve_frequency, args=camera_clock)


def horizontal_track(x_pos, line_valid, pixel_clock):
	if line_valid == 0:
		return 0
	elif pixel_clock == 1:
		return x_pos + 1
	else:
		return x_pos


camera_x.drive(horizontal_track, args=(camera_x, line_valid, pixel_clock))


def vertical_track(y_pos, line_valid, frame_invalid):
	if frame_invalid == 1:
		return 0
	elif line_valid == 1 and line_valid.down(1) == 0:
		return y_pos + 1
	else:
		return y_pos


camera_y.drive(vertical_track, args=(camera_y, line_valid, frame_invalid))


def latch(request_x, request_y, camera_x, camera_y, current_data, pixel_clock):
	if request_x == camera_x and request_y == camera_y and pixel_clock == 0:
		return current_data


response.drive(latch, args=(request_x, request_y, camera_x, camera_y, new_data, pixel_clock))

print(generate_vhdl(globals(), name="camera_example"))
print(generate_ucf(globals(), 50, 'P56'))
