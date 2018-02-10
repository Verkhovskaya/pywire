library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity camera_example is
    port(
    clock : in std_logic;
    frame_invalid : in std_logic_vector(0 to 0);
    line_valid : in std_logic_vector(0 to 0);
    pixel_clock : in std_logic_vector(0 to 0);
    new_data : in std_logic_vector(0 to 7);
    camera_clock : out std_logic_vector(0 to 0);
    response : out std_logic_vector(0 to 7));
end entity;

architecture camera_example_arch of camera_example is

signal compare_camera_clock_mask_1 : std_logic_vector(0 to 0);
signal compare_response_mask_3 : std_logic_vector(0 to 0);
signal request_y : std_logic_vector(0 to 9);
signal request_x : std_logic_vector(0 to 9);
signal compare_camera_x_2 : std_logic_vector(0 to 0);
signal compare_camera_y_3 : std_logic_vector(0 to 0);
signal line_valid_1d : std_logic_vector(0 to 0);

begin

compare_camera_clock_mask_1 <= "1" when camera_clock_mask = "1" else "0";


process(clock) begin
    if rising_edge(clock) then
        case(compare_camera_clock_mask_1) is
            when "1" => camera_clock_mask <= "0";
            when "0" => camera_clock_mask <= "1";
            when others => null;
        end case;
    end if;
end process;

compare_response_mask_1 <= "1" when request_x = camera_x else "0";


compare_response_mask_2 <= "1" when request_y = camera_y else "0";


compare_response_mask_3 <= "1" when pixel_clock = "0" else "0";


process(clock) begin
    if rising_edge(clock) then
        case(compare_response_mask_1 & compare_response_mask_2 & compare_response_mask_3) is
            when "111" => response_mask <= new_data;
            when others => null;
        end case;
    end if;
end process;

process(clock) begin
    if rising_edge(clock) then
        request_y <= "0011001000";
    end if;
end process;

process(clock) begin
    if rising_edge(clock) then
        request_x <= "0110101110";
    end if;
end process;

camera_clock <= camera_clock_mask;

compare_camera_x_1 <= "1" when line_valid = "0" else "0";


compare_camera_x_2 <= "1" when pixel_clock = "1" else "0";


process(clock) begin
    if rising_edge(clock) then
        case(compare_camera_x_1 & compare_camera_x_2) is
            when "00" => camera_x <= camera_x;
            when "10" => camera_x <= "0000000000";
            when "11" => camera_x <= "0000000000";
            when "01" => camera_x <= camera_x + 1;
            when others => null;
        end case;
    end if;
end process;

compare_camera_y_1 <= "1" when frame_invalid = "1" else "0";


compare_camera_y_2 <= "1" when line_valid = "1" else "0";


compare_camera_y_3 <= "1" when line_valid_1d = "0" else "0";


process(clock) begin
    if rising_edge(clock) then
        case(compare_camera_y_1 & compare_camera_y_2 & compare_camera_y_3) is
            when "100" => camera_y <= "0000000000";
            when "101" => camera_y <= "0000000000";
            when "110" => camera_y <= "0000000000";
            when "111" => camera_y <= "0000000000";
            when "000" => camera_y <= camera_y;
            when "001" => camera_y <= camera_y;
            when "010" => camera_y <= camera_y;
            when "011" => camera_y <= camera_y + 1;
            when others => null;
        end case;
    end if;
end process;

response <= response_mask;

process(clock) begin
    if rising_edge(clock) then
        line_valid_1d <= line_valid;
    end if;
end process;

end camera_example_arch;