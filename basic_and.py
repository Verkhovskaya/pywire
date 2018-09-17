from pywire import *


def invert(signal):
    if signal:
        return False
    else:
        return True


class Inverter:
    def __init__(self, a, b):
        b.drive(invert, a)

width = 4
a = Signal(width, io="in")
b = Signal(width, io="out")
Inverter(a, b)
build()