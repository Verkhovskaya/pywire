from pywire import *

camera_clock = Signal(1, io="out", port="P40")  # 25MHz


def halve_frequency(slow_clock):
    return not slow_clock


# MojoV3 clock is 50MHz, camera_clock is 25 MHz.
camera_clock.drive(halve_frequency, camera_clock)


# Timing signals incoming from camera
frame_invalid = Signal(1, io="in", port="P26")  # New frame trigger coming from camera. Aka VSYNC
line_valid = Signal(1, io="in", port="P34")  # New line trigger coming from camera. AKA HREF
pixel_clock = Signal(1, io="in", port="P23")  # New pixel trigger coming from camera. AKA PCLK


def _(x):
    return x


def invert(x):
    return not x


# pixel_clock (1 cycle down), line_valid (1 cycle down) and frame_valid (no clock)
pixel_clock_1d = Signal(1)
pixel_clock_1d.drive(_, pixel_clock)
line_valid_1d = Signal(1)
line_valid_1d.drive(_, line_valid)
frame_valid = Signal(1)
frame_valid.drive(invert, frame_invalid, clock=False)

"""
camera_x = Signal(10)  # Derived from pixel_clock, pixel_clock_1d, line_valid
camera_y = Signal(10)  # Derived from pixel_clock, pixel_clock_1d, line_valid, line_valid_1d, frame_invalid


def increment_on_rising(current_value, driving_signal, driving_signal_1d, clear):
    if clear:
        return 0
    elif driving_signal and not driving_signal_1d:
        return current_value + 1


camera_x.drive(increment_on_rising, (camera_x, pixel_clock, pixel_clock_1d, line_valid))
camera_y.drive(increment_on_rising, (camera_y, line_valid, line_valid_1d, frame_invalid))

# 8 bit RGB data coming from the camera
new_data = Signal(8, io="in", port=['P9', 'P11', 'P7', 'P14', 'P5', 'P16', 'P2', 'P21'])
get_camera_x = Signal(10, io="in")
get_camera_y = Signal(10, io="in")
response = Signal(8, io="out", port=["P134", "P133", "P132", "P131", "P127", "P126", "P124", "P123"])


def update_response(camera_data, camera_x, camera_y, get_camera_x, get_camera_y):
    if camera_x == get_camera_x and camera_y == get_camera_y:
        return camera_data


response.drive(update_response, (new_data, camera_x, camera_y, get_camera_x, get_camera_y))


"""
rename_signals(globals())
build()
#launch_test()
#print(generate(name="blink_example"))
