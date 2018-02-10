library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity blink_example is
    port(
    clock : in std_logic;
    led1 : out std_logic_vector(0 to 0));
end entity;

architecture blink_example_arch of blink_example is

signal compare_counter_1 : std_logic_vector(0 to 0);
signal compare_led1_mask_1 : std_logic_vector(0 to 0);

begin

led1 <= led1_mask;

compare_counter_1 <= "1" when counter > 33554432 else "0";


process(clock) begin
    if rising_edge(clock) then
        counter <= "1";
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