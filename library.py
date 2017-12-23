from collections import namedtuple
import builder as builder


# Helper functions
def as_list(something):
	if isinstance(something, list):
		return something
	else:
		return [something]


def as_bit_array(bit_or_data):
	if isinstance(bit_or_data, Data) or isinstance(bit_or_data, list):
		return bit_or_data
	else:
		return [bit_or_data]


def i(some_string):
	return int(some_string, 2)


def b(some_int):
	return bin(some_int)[2:]


def pad(number, size):
	return "0"*(size-len(number))+str(number)


class SignalBit:
	def __init__(self, index, parent):
		self.parent = parent
		self.index = index
		self.driver = None

	def info(self):
		if self.driver:
			return "#"
		else:
			return "?"

	def bind(self, inputs, driver_function):
		print self
		print inputs
		self.driver = (inputs, driver_function)


class Data:
	def __init__(self, size, initial=None, name=None):
		self.initial = initial
		self.bits = [SignalBit(self, x) for x in range(size)]
		self.name = name

	def __getitem__(self, index):
		return self.bits[index]

	def __len__(self):
		return len(self.bits)

Port = namedtuple('Port', ['signal', 'direction'])


# The programmatic interface
class Entity:
	def __init__(self, frequency):
		self.frequency = frequency
		self.signals = []
		self.ports = []

	def build(self, inputs, driver_function, outputs):
		inputs, outputs = as_list(inputs), as_list(outputs)
		for each in inputs + outputs:
			if each not in self.signals:
				self.signals.append(each)
		for out_signal in as_list(outputs):
			out_signal_index = outputs.index(out_signal)
			for out_bit_index in range(len(as_bit_array(out_signal))):
				select_output = (lambda x: pad(driver_function(x)[out_signal_index], len(out_signal))[out_bit_index])
				as_bit_array(out_signal)[out_bit_index].bind(inputs, select_output)

	def port(self, signal, direction):
		self.ports.append(Port(signal, direction))

	def generate_vhdl(self):
		return builder.generate_vhdl(self)

	def generate_ucf(self):
		return builder.generate_ucf(self)

	def generate_bin(self):
		return builder.generate_bin(self)