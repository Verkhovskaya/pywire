from pywire import *

counter = Signal(26)
led1 = Signal(1, io="out", port="P134")

def logic(counter, led):
	counter += 1
	if counter > 2**25:
		led1 = 1
	else:
		led1 = 0


build(logic, (counter, led1))

print(generate_vhdl(globals(), name="blink_example"))
print(generate_ucf(globals(), 50, 'P56'))