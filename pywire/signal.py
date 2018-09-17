import ast
import inspect

from .vhdl_utils import as_string
from .shared_utils import to_list


class Signal:
    all_signals = []

    def __init__(self, bit_size, io=None, port=None, signed=False):
        self.size = int(bit_size)
        self.io = io
        self.name = "signal_" + str(len(Signal.all_signals)+1)
        self.index = len(self.all_signals)
        self.all_signals.append(self)
        if port is not None:
            if type(port) is tuple or type(port) is list:
                self.port = port
            else:
                self.port = [port]
        else:
            self.port = None
        self.driving_function = None
        self.driving_logic = None
        self.driving_signals = None
        self.clock = None

        self.current_val = 0

        self.signed = signed

    def drive(self, logic, input_signals=None, clock=True):
        try:
            assert callable(logic)
        except AssertionError:
            raise Exception("logic argument passed to Signal.build must be a function:")
        self.driving_function = logic
        self.driving_logic = ast.parse(inspect.getsource(logic))
        self.clock = clock
        self.driving_signals = to_list(input_signals)

    def __len__(self):
        return self.size

    def __eq__(self, other):
        return as_string(self) + " = " + as_string(other)

    def __trunc__(self):
        return self.current_val

    def __add__(self, other):
        return str(self) + " + " + str(other)

    def __radd__(self, other):
        return str(other) + " + " + str(self)

    def __mul__(self, other):
        return str(self) + " * " + str(other)

    def __rmul__(self, other):
        return str(other) + " * " + str(self)

    def __sub__(self, other):
        return str(self) + " - " + str(other)

    def __rsub__(self, other):
        return str(other) + " - " + str(self)

    def delay(self, num):
        new_name = self.name + "_1d"
        if new_name not in globals().keys():
            new_signal = Signal(1).drive(self)
            new_signal.name = new_name
            globals()[new_name] = new_signal
        return new_name
