# PyDL
(Pronounced fiddle)
An easy-to-use Python library for generating VHDL. 
### Supports FPGA components, including:
- Look-up tables
- Logic slices
- BRAM

### Other features include:
- Generating .ucf files

(Support for re-usable, configurable components coming soon)

### Does not support:
- Using more than one clock

### Sections in this documentation:
[Blink example](https://github.com/Verkhovskaya/Valerian/new/master?readme=1#blink-example) (Look-up tables, logic slices and generating .vhdl and .ucf files)

[BRAM](https://github.com/Verkhovskaya/Valerian/new/master?readme=1#bram) (Look-up tables, logic slices and generating .vhdl and .ucf files)

# Blink example
Valerian is based on a `Signal` class, which contains an integer value between 0 and 2**(size)-1. It is initialized as 

```python
Signal(bit_size, io=None, port=None, name=None)
```

During each clock cycle (~50 million/second), each Signal is set to the result of function. This function is assigned to the signal with
```python
my_signal.drive(my_func, args=(arg1, arg2, ...))
```

For example:
```python
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
```
Which generates:
```vhdl
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity generated_top is
    port(
    clock : in std_logic;
    led1 : out std_logic_vector(0 to 0));
end entity;

architecture generated_arch of generated_top is

signal counter : std_logic_vector(0 to 25);
signal compare_led1_mask_1 : std_logic_vector(0 to 0);

begin

led1 <= led1_mask;

process(clock) begin
    if rising_edge(clock) then
        counter <= counter + 1;
    end if;
end process;

compare_led1_mask_1 <= "1" when counter > 33554432 else "0";


process(clock) begin
    if rising_edge(clock) then
        case(compare_led1_mask_1) is
            when "0" => led1_mask <= "0";
            when "1" => led1_mask <= "1";
            when others => null;
        end case;
    end if;
end process;

end generated_arch;
```

If you are testing on Xilinx hardware, you will also need to create a .ucf file that tells the FPGA how to connect the outputs to the pins. 
My hardware uses an external clock on pin 56 that runs at 50MHz/second, so I use

```python
print(generate_ucf(globals(), 50, 'P56'))
```
Which outputs
```ucf
end generated_arch;
NET "clock" TNM_NET = clock;
TIMESPEC TS_clk = PERIOD "clock" 50 MHz HIGH 50%;
NET "clock" LOC = P56 | IOSTANDARD = LVTTL;
NET "led1<0>" LOC = P134 | IOSTANDARD = LVTTL;
```

Built with ISE and loaded onto a MojoV3, this creates a blinking light: [YouTube link](https://www.youtube.com/watch?v=y5rW_DIoK7Y&feature=youtu.be)

# BRAM
BRAM is initialized with `BRAM(width, depth, a_write=True, a_read=True, b_write=False, b_read=False)`. 

For example, to create a 32x512 dual ported BRAM:

```python
mem = BRAM(32, 512, True, True, True, True)

# Pins:
mem.a_address
mem.a_write_en
mem.a_data_in
mem.a_data_out
mem.b_address
mem.b_write_en
mem.b_data_in
mem.b_data_out

# Properties:
mem.width
mem.depth
mem.props  # {"a_write":a_write, "a_read":a_read, "b_write":b_write, "b_read":b_read}
mem.id
