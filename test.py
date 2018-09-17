from pywire import *


def increment(x):
    return x+1


clock_counter = Signal(26)
clock_counter.drive(increment, clock_counter)


def get_top_bit(x):
    if x > (2**25):
        return True
    else:
        return False


flipping_bit = Signal(1, signed=None)
flipping_bit.drive(get_top_bit, clock_counter)


def identity(x):
    return x


same = Signal(1, io="out", port="P134")
same.drive(identity, flipping_bit)


def invert(x):
    if x:
        return False
    else:
        return True


inverted = Signal(1, io="out", port="P133")
inverted.drive(invert, flipping_bit)


class OneZeroOneZero(Component):
    def __init__(self, led_signals):
        Component.__init__(self)
        self.led_signals = led_signals

    def header(self):
        return "signal custom_vhdl: std_logic_vector(0 to 3);\n"

    def body(self):
        body = 'custom_vhdl <= "1010";\n'
        for x in range(4):
            body += self.led_signals[x].name + " <= custom_vhdl(" + str(x) + " to " + str(x) + ");\n"
        return body


pins = []
for pin in ["P127", "P126", "P124", "P123"]:
    pins.append(Signal(1, io="out", port=pin))
OneZeroOneZero(pins)

rename_signals(globals())
build()
