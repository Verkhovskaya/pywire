from valerian import *

counter = Signal(26)


def increment(x):
    return x+1


counter.drive(increment, args=(counter))


led1 = Signal(1, io="out", port="P134")

def blink(slow_clock):
    if slow_clock > 2**25:
        return 1
    else:
        return 0


led1.drive(blink, args=(counter))

print(generate_vhdl(globals()))
print(generate_ucf(globals(), 50, 'P56'))