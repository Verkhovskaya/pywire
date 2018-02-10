library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity component_example is
    port(
    clock : in std_logic;
    a_outer : in std_logic_vector(0 to 0);
    b_outer : out std_logic_vector(0 to 0));
end entity;

architecture component_example_arch of component_example is

component inverter is
    clock : in std_logic;
    a : in std_logic_vector (0 to 0);
    b : out std_logic_vector (0 to 0));
end component;
signal b_outer_mask : std_logic_vector(0 to 0);

begin

COMPONENT_1 : inverter
port map (
    a => a_outer;
    b => b_outer_mask;
    clock => clock;
);

b_outer <= b_outer_mask;

end component_example_arch;