from pywire import *
mem = BRAM(8, 2, True, True)

bram_address = Signal(1, io="in", port="P51")
bram_write_data = Signal(8, io="in", port=["P35", "P33", "P30", "P27", "P24", "P22", "P17", "P15"])
bram_write_en = Signal(1, io="in", port="P41")
bram_read = Signal(8, io="out", port=["P134", "P133", "P132", "P131", "P127", "P126", "P124", "P123"])

def identity(x):
    return x


mem.a_address.drive(identity, bram_address)
mem.a_data_in.drive(identity, bram_write_data)
mem.a_write_en.drive(identity, bram_write_en)
bram_read.drive(identity, mem.a_data_out)

rename_signals(globals())
print(generate(name="bram_example"))
#print(timing(globals(), 50, 'P56', vendor="Xilinx"))