library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity bram_example is
    port(
    clock : in std_logic;
    bram_address : in std_logic_vector(0 to 0);
    bram_write_data : in std_logic_vector(0 to 7);
    bram_write_en : in std_logic_vector(0 to 0);
    bram_read : out std_logic_vector(0 to 7));
end entity;

architecture bram_example_arch of bram_example is

type ram_type_1 is array (1 downto 0) of std_logic_vector(7 downto 0);
shared variable RAM_1 : ram_type_1 := (others => (others => '0'));
signal BRAM_1_a_data_in : std_logic_vector(0 to 7);
signal BRAM_1_a_data_out : std_logic_vector(0 to 7);
signal BRAM_1_a_write_en : std_logic_vector(0 to 0);
signal BRAM_1_a_address : std_logic_vector(0 to 0);
signal bram_read_mask : std_logic_vector(0 to 7);

begin

process(clock) begin
    if rising_edge(clock) then
        BRAM_1_a_data_out <= RAM_1(conv_integer(BRAM_1_a_address));
        if BRAM_1_a_write_en = "1" then
            RAM_1(conv_integer(BRAM_1_a_address)) := BRAM_1_a_data_in;
        end if;
    end if;
end process;

process(clock) begin
    if rising_edge(clock) then
        BRAM_1_a_data_in <= bram_write_data;
    end if;
end process;


process(clock) begin
    if rising_edge(clock) then
        BRAM_1_a_write_en <= bram_write_en;
    end if;
end process;

process(clock) begin
    if rising_edge(clock) then
        BRAM_1_a_address <= bram_address;
    end if;
end process;

bram_read <= bram_read_mask;

process(clock) begin
    if rising_edge(clock) then
        bram_read_mask <= BRAM_1_a_data_out;
    end if;
end process;

end bram_example_arch;