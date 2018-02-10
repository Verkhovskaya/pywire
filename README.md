# Pywire

An easy-to-use Python 2.7 library for generating VHDL.

### Supports all main FPGA components, including:
- Look-up tables
- Logic slices
- BRAM

### Other features include:
- Generating .ucf files

(Support for import VHDL components coming soon)

### Does not support:
- Using more than one clock

### Sections in this documentation:
[Blink example](https://github.com/Verkhovskaya/Pywire/new/master?readme=1#blink-example) (Look-up tables, logic slices and generating .vhdl and .ucf files)

[BRAM](https://github.com/Verkhovskaya/Pywire/new/master?readme=1#bram)

# Blink example
Pywire is based on a `Signal` class, which contains an integer value between 0 and 2**(size)-1. It is initialized as 

```python
Signal(bit_size, io=None, port=None, name=None)
```

During each clock cycle (~50 million/second), each Signal is set to the result of function. This function is assigned to the signal with
```python
my_signal.drive(my_func, args=(arg1, arg2, ...))
```

For example:
```python
from pywire import *

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
```

If you are testing on Xilinx hardware, you will also need to create a .ucf file that tells the FPGA how to connect the outputs to the pins. 
My hardware uses an external clock on pin 56 that runs at 50MHz/second, so I use

```python
print(generate_ucf(globals(), 50, 'P56'))
```

Built with ISE and loaded onto a MojoV3, this creates a blinking light: [YouTube link](https://www.youtube.com/watch?v=y5rW_DIoK7Y&feature=youtu.be)

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
