from pywire import *

component_text = """
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity inverter is
    port(
    clock : in std_logic_vector(0 to 0);
    a : in std_logic_vector(0 to 0);
    b : out std_logic_vector(0 to 0));
end entity;

architecture inverter_arch of inverter is

begin

	b <= not a;
	
end inverter_arch;
"""

a_out = Signal(1, name="a_outer", io="in", port=["P1"])
b_out = Signal(1, name="b_outer", io="out", port=["P2"])

inverter = FromText(component_text, {"a": a_out, "b": b_out})

print(vhdl(globals(), name="component_example"))
print(timing(globals(), 50, 'P56', vendor="Xilinx"))