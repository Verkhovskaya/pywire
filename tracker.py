from signal_v2 import Signal
from builder_v2 import generate_vhdl
from camera_pos import Camera_pos

# Camera interface
new_frame = Signal(1, io="in")
new_line = Signal(1, io="in")
new_pixel = Signal(1, io="in")
y_pos = Signal(10)
x_pos = Signal(10)
pixel_data = Signal(8, io="in")

camera = Camera_pos(links=(("newFrame", new_frame), ("newLine", new_line), ("newPixel", new_pixel), ("yPos", y_pos), ("xPos", x_pos)))

def increment(current, increment_by, do_increment):
	if do_increment:
		return current + increment_by
	else:
		return current


do_increment = Signal(1, name="do_increment")
do_increment.drive(1)
center_x = Signal(3, name="center_x")
center_y = Signal(9, name="center_y")
total_x = Signal(5, name=total_x)
total_y = Signal(5, name=total_y)
total_points =




center_x.drive(increment, args=(center_x, center_y, do_increment))

print generate_vhdl(center_x)