# BRAM
BRAM is initialized with 
```python
mem = BRAM(width, depth, a_write=True, a_read=True, b_write=False, b_read=False)`. 

# Pins:
mem.a_address
mem.a_write_en  # Only implemented if a_write == True
mem.a_data_in  # Only implemented if a_write == True
mem.a_data_out  # Only implemented if a_read == True
mem.b_address  # Only implemented if b_write == True or b_read == True
mem.b_write_en  # Only implemented if b_write == True
mem.b_data_in  # Only implemented if b_write == True
mem.b_data_out  # Only implemented if b_read == True

# Properties:
mem.width
mem.depth
mem.props  # {"a_write":a_write, "a_read":a_read, "b_write":b_write, "b_read":b_read}
mem.id
```

So for example, a single port 8x2 BRAM:

```python
from pywire import *
mem = BRAM(8, 2, True, True)

bram_address = Signal(1, io="in", port="P51")
bram_write_data = Signal(8, io="in", port=["P35", "P33", "P30", "P27", "P24", "P22", "P17", "P15"])
bram_write_en = Signal(1, io="in", port="P41")
bram_read = Signal(8, io="out", port=["P134", "P133", "P132", "P131", "P127", "P126", "P124", "P123"])

mem.a_address.drive(bram_address)
mem.a_data_in.drive(bram_write_data)
mem.a_write_en.drive(bram_write_en)
bram_read.drive(mem.a_data_out)

print(generate_vhdl(globals()))
print(generate_ucf(globals(), 50, 'P56'))
```
