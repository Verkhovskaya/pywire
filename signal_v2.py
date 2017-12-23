def match_widths(some_string, some_object):
	ret = []
	for each in some_object:
		ret.append(some_string[:len(each)])
		some_string = some_string[len(each):]
	return ret


class Signal:
	def __init__(self, bit_size, io=None, name=None):
		# Temporary
		self.current_val = None
		self.was_used = None

		self.size = bit_size
		self.io = io
		self.driver = None
		self.driver_simple = None
		self.input_signals = None
		self.uses_signals = None
		self.clock = None
		if name:
			self.name = name
		else:
			self.name = None

	def drive(self, func, args=None, clock=None):
		self.clock = None
		if not args:
			self.driver = func
		else:
			total_width = sum([len(x) for x in args])
			self.driver = {}
			for i in range(len(args)):
				args[i].was_used = False
			for i in range(2**total_width):
				func_input_line = match_widths(bin(i)[2:].zfill(total_width), args)
				for j in range(len(args)):
					args[j].current_val = func_input_line[j]
				func_output = func(*args)
				if func_output not in self.driver.keys():
					self.driver[func_output] = [func_input_line]
				else:
					self.driver[func_output].append(func_input_line)
			self.input_signals = args
			self.uses_signals = filter(lambda x: x.was_used, self.input_signals)

			total_width = sum([len(x) for x in self.uses_signals])
			self.driver_simple = {}
			for i in range(2**total_width):
				func_input_line = match_widths(bin(i)[2:].zfill(total_width), self.uses_signals)
				for j in range(len(self.uses_signals)):
					self.uses_signals[j].current_val = func_input_line[j]
				func_output = func(*args)
				if func_output not in self.driver_simple.keys():
					self.driver_simple[func_output] = [func_input_line]
				else:
					self.driver_simple[func_output].append(func_input_line)
		if not self.name:
			self.name = str(hash(self))

	def __len__(self):
		return self.size

	def __add__(self, other):
		return ("+", self, other)

	def __nonzero__(self):
		self.was_used = True
		return len(filter(lambda x: x != "0", self.current_val)) != 0

	def __int__(self):
		self.was_used = True
		return int(self.current_val, 2)

	def __str__(self):
		self.was_used = True
		return self.current_val.zfill(self.size)

	def generate(self):
		if type(self.driver) is tuple:
			print(self.driver)
		elif type(self.driver) is str:
			print(self.driver)
		else:
			for each in self.driver:
				print(str(each) + ": " + ",".join(self.driver[each]))


class Component:
	def __init__(self, signals):
		self.signals = signals

	def link(self, links):
		return links