from pywire.signal import Signal
from tkinter import *
from tkinter.ttk import Separator
from enum import Enum

class BitState(Enum):
    TRUE = 1
    FALSE = 2
    TRUE_FORCED = 3
    FALSE_FORCED = 4
    UNDEFINED = 5


def bitsToInt(bit_array):
    for bit in bit_array:
        if bit.state == BitState.UNDEFINED:
            return None
    total = 0
    for index in range(len(bit_array)):
        bit = bit_array[index]
        total *= 2
        if bit.state == BitState.TRUE_FORCED or bit.state == BitState.TRUE:
            total += 1
    return total


class Bit:
    def press(self):
        print("PRESSED")
        if self.state == BitState.UNDEFINED:
            self.state = BitState.TRUE_FORCED
        elif self.state == BitState.TRUE_FORCED:
            self.state = BitState.FALSE_FORCED
        elif self.state == BitState.FALSE_FORCED:
            self.state = BitState.UNDEFINED
        elif self.state == BitState.TRUE:
            self.state = BitState.TRUE_FORCED
        elif self.state == BitState.FALSE:
            self.state = BitState.TRUE_FORCED
        else:
            raise Exception("WTF")

        self.update_gui()

    def update_gui(self):
        if self.state == BitState.UNDEFINED:
            self.entity.configure(text="UN")
        elif self.state == BitState.TRUE_FORCED:
            self.entity.configure(text="TF")
        elif self.state == BitState.FALSE_FORCED:
            self.entity.configure(text="FF")
        elif self.state == BitState.TRUE:
            self.entity.configure(text="T_")
        elif self.state == BitState.FALSE:
            self.entity.configure(text="F_")
        else:
            raise Exception("WTF: " + str(self.state))

    def __init__(self, master, row, column):
        self.entity = Button(master,
                             command=self.press)
        self.entity.grid(row=row, column=column)
        self.state = BitState.FALSE
        self.update_gui()


def refresh():
    globals()["app"].recalculate_states()


class Application(Frame):
    def draw_signals(self, master, signals, start_row):
        for signal in signals:
            self.bits[signal.name] = [[None for bit_index in range(len(signal))] for t in range(self.time)]
            print("LABEL")
            Label(master, text=signal.name).grid(row=start_row, column=1)
            for bit_index in range(len(signal)):
                Label(master, text="<" + str(bit_index) + ">").grid(row=start_row, column=2)
                for time_stamp in range(self.time):
                    self.bits[signal.name][time_stamp][bit_index] = Bit(master, start_row, time_stamp + 3)
                    Separator(master, orient="horizontal").grid(row=start_row, column=time_stamp + 3, sticky=S + W + E)
                start_row += 1
            start_row += 1
        print("done")

    def createLayout(self, master):
        Button(master, text="Refresh", command=refresh).grid(row=0, column=0)
        for x in range(self.time):
            Label(master, text="t=" + str(x)).grid(row=1, column=x+3)
        row = 2
        if self.input_signals:
            Label(master, text="inputs").grid(row=row, column=0)
            self.draw_signals(master, self.input_signals, row)
            row += sum([len(signal) for signal in self.input_signals])+3
            Label(master, text=" ").grid(row=row-1, column=0)

        if self.other_signals:
            Label(master, text="other").grid(row=row, column=0)
            self.draw_signals(master, self.other_signals, row)
            row += sum([len(signal) for signal in self.other_signals]) + 3
            Label(master, text=" ").grid(row=row-1, column=0)

        if self.output_signals:
            Label(master, text="outputs").grid(row=row, column=0)
            self.draw_signals(master, self.output_signals, row)
            row += sum([len(signal) for signal in self.output_signals]) + 3
            Label(master, text=" ").grid(row=row-1, column=0)

    def recalculate_states(self):
        for time_stamp in range(0, self.time):
            for signal in Signal.all_signals:
                if signal.driving_signals:
                    input_states = []
                    for input_signal in signal.driving_signals:
                        if signal.clock:
                            input_bits = self.bits[input_signal.name][time_stamp-1]
                        else:
                            input_bits = self.bits[input_signal.name][time_stamp]
                        input_states.append(bitsToInt(input_bits))
                    output_val = signal.driving_function(*input_states)
                    if isinstance(output_val, int):
                        output_string = bin(output_val)[2:].rjust(len(signal), "0")
                        output_string = output_string[len(output_string)-len(signal):]
                        print(output_string)
                        output_bool_array = [letter == "1" for letter in output_string]
                        print(output_bool_array)
                        signal_bits = self.bits[signal.name][time_stamp]
                        for index in range(len(output_bool_array)):
                            if signal_bits[index].state == BitState.TRUE_FORCED:
                                pass
                            elif signal_bits[index].state == BitState.FALSE_FORCED:
                                pass
                            elif output_bool_array[index]:
                                signal_bits[index].state = BitState.TRUE
                            else:
                                signal_bits[index].state = BitState.FALSE
                    elif isinstance(output_val, bool):
                        for index in range(len(output_bool_array)):
                            if output_val:
                                signal_bits[index] = BitState.TRUE
                            else:
                                signal_bits[index] = BitState.FALSE
                    else:
                        raise Exception("Function output is not a boolean or int")

        for signal in Signal.all_signals:
            for bit_row in self.bits[signal.name]:
                for bit in bit_row:
                    bit.update_gui()

    def __init__(self, master=None):
        self.bits = {}
        self.time = 10
        signals = Signal.all_signals
        self.input_signals = list(filter(lambda x: x.io == "in", signals))
        self.output_signals = list(filter(lambda x: x.io == "out", signals))
        self.other_signals = list(filter(lambda x: not x.io, signals))
        Frame.__init__(self, master)
        print("Creating layout")
        self.createLayout(master)
        print("DONE")
        self.recalculate_states()


def launch_test():
    root = Tk()
    app = Application(master=root)
    globals()["app"] = app
    app.mainloop()
    root.destroy()

"""


class TestObject:
    def __init__(self, signals=Signal.all_signals, inputs={}, turns=10):
        self.all_signals = signals
        self.in_signals = list(filter(lambda x: x.io == "in", signals))
        self.out_signals = list(filter(lambda x: x.io == "out", signals))


    def print(self, turn, signals=self.signals):
"""