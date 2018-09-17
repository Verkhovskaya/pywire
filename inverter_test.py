from pywire import *

class Inverter(Component):
    count = 0

    @staticmethod
    def identity(x):
        return x

    def __init__(self, size, signal_in, signal_out):
        Component.__init__(self)
        Inverter.count += 1
        self.id = Inverter.count
        self.size = size
        self.signal_in = signal_in
        self.signal_out = signal_out

    def header(self):
        return """
            component inverter is
                generic (N: positive);
                port(
                    clock : in std_logic_vector(0 to 0);
                    a, b  : in_std_logic_vector(0 to N-1));
            end component;
        """

    def body(self):
        return "INVERTER_" + str(self.id) + " : inverter \n" +\
            "generic map (N => " + str(self.size) + ")\n port map (" +\
                self.signal_in.name + ", " + self.signal_out.name + ")\n"


width = 4
a = Signal(width, io="in")
b = Signal(width, io="out")
Inverter(width, a, b)
print(generate())