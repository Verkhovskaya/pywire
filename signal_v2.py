import ast
import inspect
import math
import random


class Signal:
	signal_count = 1

	def __init__(self, bit_size, type="lut", name=None):
		bit_size = int(bit_size)
		self.size = int(bit_size)
		self.type = type
		if name:
			self.name = name
		else:
			self.name = "gen_" + str(self.signal_count)
			self.signal_count += 1

		self.func = None
		self.args = None
		self.clock = None
		self.map = None

		self.current_val = "0"*bit_size

	def io(self, map_to):
		if type(map_to) is tuple or type(map_to) is list:
			self.map = map_to
		else:
			self.map = [map_to]

	def drive(self, func, args=None, clock=True):
		self.func = func
		self.args = args
		self.clock = clock

	def __str__(self):
		return str(self.current_val)

	def __int__(self):
		return int(self.current_val, 2)

	def __bool__(self):
		return self.current_val == "1"

	def __len__(self):
		return self.size


class BinOperation:
	def __init__(self, operation, value):
		self.operation = operation
		self.value = value

	def __add__(self, other):
		return MathOperation("+", self, other)

	def __str__(self):
		if isinstance(self.value, Signal):
			return self.value.name
		else:
			raise Exception("This should not have happened")


def do_bin(value):
	return BinOperation('bin', value)


def do_int(value):
	return BinOperation('int', value)


def do_str(value):
	return BinOperation('value', value)


class MathOperation:
	def __init__(self, operation, val1, val2):
		self.operation = operation
		self.val1 = val1
		self.val2 = val2

	def __add__(self, other):
		return MathOperation("+", self, other)

	def __str__(self):
		return str(self.val1) + " " + self.operation + " " + str(self.val2)


def generate_header(signals):
	io_signals = list(filter(lambda x: x.type in ["in", "out"], signals))
	io_texts = [x.name + " : " + x.type + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in io_signals]
	text = "library ieee;\n"
	text += "use ieee.std_logic_1164.all;\n\n"
	text += "entity generated is\n"
	text += "port(\n"
	text += ";\n".join(["clock : in std_logic"]+io_texts)
	text += ");\n"
	text += "end entity;\n\n"
	return text


def get_all_entity_signals(*nodes):
	if type(nodes) is not list:
		if type(nodes) is tuple:
			nodes = list(*nodes)
		else:
			nodes = [nodes]
	unseen_signals = nodes
	seen_signals = []
	while unseen_signals:
		current = unseen_signals.pop()
		seen_signals.append(current)
		if current.args:
			for drive_input in current.args:
				if isinstance(drive_input, Signal):
					if drive_input not in seen_signals:
						unseen_signals.append(drive_input)
	return seen_signals


def to_direct_assignment(new_val):
	if type(new_val) is str:
		return '"' + new_val + '"'
	elif type(new_val) is int:
		return str(new_val)
	elif isinstance(new_val, Signal):
		return new_val.name
	elif isinstance(new_val, BinOperation):
		return str(new_val)
	elif isinstance(new_val, MathOperation):
		return str(new_val)
	else:
		raise Exception("Direct assignment bad value: " + str(new_val))


def get_driving_indexes(signal):
	tree = ast.parse(inspect.getsource(signal.func))
	all_input_signals = [x.id for x in tree.body[0].args.args]
	driving_signals = []
	for node in ast.walk(tree):
		if isinstance(node, ast.If):
			for subnode in ast.walk(node.test):
				if isinstance(subnode, ast.Name):
					if subnode.id in all_input_signals:
						driving_signals.append(subnode.id)
	indexes = sorted([all_input_signals.index(x) for x in driving_signals])
	return indexes


def match_widths(some_string, some_object):
	ret = []
	for each in some_object:
		ret.append(some_string[:len(each)])
		some_string = some_string[len(each):]
	return ret


def get_lut(destination, driving_signals):
	total_width = sum([len(x) for x in driving_signals])
	lut = {}
	for i in range(2 ** total_width):
		func_input_line = match_widths(bin(i)[2:].zfill(total_width), driving_signals)
		for j in range(len(driving_signals)):
			driving_signals[j].current_val = func_input_line[j]
		func_output = destination.func(*destination.args)
		if func_output not in lut.keys():
			lut[func_output] = [func_input_line]
		else:
			lut[func_output].append(func_input_line)
	return lut


def get_logic(driven, driving_indexes):
	driving_signals = [driven.args[x] for x in driving_indexes]
	lut = get_lut(driven, driving_signals)
	text = "case(" + " & ".join([x.name for x in driving_signals]) + ") is\n"
	for each in lut.keys():
		if each != None:
			for input in lut[each]:
				text += "when \"" + "".join(input) + "\" => " + driven.name + " <= " + to_direct_assignment(each) + ";\n"
	text += "end case;\n"
	return text


def identity(*args):
	return "000"


def change_return_logic(signal):
	return_nodes = []
	tree = ast.parse(inspect.getsource(signal.func))
	func_name = tree.body[0].name
	for node in ast.walk(tree):
		if isinstance(node, ast.Return):
			return_nodes.append(node)
	for node in return_nodes:
		for subnode in ast.walk(node):
			try:
				if subnode.id == 'int':
					subnode.id = 'do_int'
				elif subnode.id == 'str':
					subnode.id = 'do_str'
				elif subnode.id == 'bin':
					subnode.id = 'do_bin'
			except:
				pass
	exec(compile(tree, filename="<ast>", mode="exec"))
	signal.func = (eval(func_name))


def indent(in_text):
	level = 0
	in_text = in_text.split("\n")
	out_text = []
	for each in in_text:
		each = each.strip()
		if " " in each:
			first_word = each[:each.replace("(", " (").index(" ")]
		else:
			first_word = each
		if first_word in [");", "end", "begin"]:
			level -= 1
		out_text.append("    "*level + each)
		if first_word in ("entity", "port", "begin", "if", "case", "process"):
			level += 1
	return "\n".join(out_text)

def generate_return(node, arg_mappings):
	pass


def generate_logic(node, arg_mappings):
	print(ast.dump(node))


def generate_vhdl(*nodes):
	entity_signals = get_all_entity_signals(nodes)
	text = generate_header(entity_signals)
	text += "architecture generated_arch of generated is\n\n"
	print("Header complete")
	for signal in entity_signals:
		if signal.type != "in":
			if signal.clock:
				text += "process(clock) is\n"
				text += "if rising_edge(clock) then\n"
			if signal.args:
				tree = ast.parse(inspect.getsource(signal.func))
				arg_names = [x.id for x in tree.body[0].args.args]
				arg_mappings = {arg_names[x]: signal.args[x].name for x in range(len(arg_names))}
				generate_logic(tree.body[0], arg_mappings)
				print arg_mappings
				driving_indexes = get_driving_indexes(signal)
				change_return_logic(signal)
				text += get_logic(signal, driving_indexes)
			else:
				if signal.func:
					text += signal.name + " <= " + to_direct_assignment(signal.func) + ";\n"
			print("Signal " + signal.name + " complete")
			if signal.clock:
				text += "end if;\n"
				text += "end process;\n"
			text += "\n"
	text += "end generated_arch;"
	text = indent(text)
	print("")
	print(text)
	return text


def generate_ucf(frequency, *nodes):
	entity_signals = get_all_entity_signals(nodes)
	text = 'NET "clock" TNM_NET = clock;\n'
	text += 'TIMESPEC TS_clk = PERIOD "clock" ' + str(frequency) + ' MHz HIGH 50%;\n'
	for signal in entity_signals:
		if signal.map:
			for x in range(len(signal.map)):
				text += 'NET ' + signal.name + '<' + str(x) + '> LOC = ' + signal.map[x] + ' | IOSTANDARD = LVTTL;\n'
	return text


new_data = Signal(8, type="in", name="new_data") # 8 bit RGB data coming from the camera
new_line = Signal(1, type="in", name="new_line")  # New line trigger coming from camera
new_frame = Signal(1, type="in", name="new_frame") # New frame trigger coming from camera
new_pixel = Signal(1, type="in", name="new_pixel") # New pixel trigger coming from camera

camera_x = Signal(4, name="camera_x") # Derived from new_frame, new_line
camera_y = Signal(4, name="camera_y") # Derived from new_line, new_pixel

request_x = Signal(4, name="request_x")
request_y = Signal(4, name="request_y")
response = Signal(8, type="out", name="response")


request_x.drive(430)
request_y.drive(200)


def camera_pos(current, increment, clear):
	if int(clear) == 1:
		return 0
	elif int(increment) == 1:
		return int(current) + 1
	else:
		return int(current)


camera_x.drive(camera_pos, args=(camera_x, new_pixel, new_line))
camera_y.drive(camera_pos, args=(camera_y, new_line, new_frame))


def latch(request_x, request_y, current_x, current_y, current_data):
	if int(request_x) == int(current_x) and int(request_y) == int(current_y):
		return current_data

response.drive(latch, args=(request_x, request_y, camera_x, camera_y, new_data), clock=False)

response.io("p11")
new_data.io(["p"+str(x) for x in range(8)])
new_pixel.io("p8")
new_line.io("p9")
new_frame.io("p10")
generate_vhdl(response)
print("")
print(generate_ucf(50, response))