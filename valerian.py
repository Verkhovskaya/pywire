import ast
import inspect
import math
import random
import copy


"""
General code structure:

Signal class (Data storage for library access)
Several Operator classes


"""


class Signal:
	all_signals = []

	def __init__(self, bit_size, type="lut"):
		self.size = int(bit_size)
		self.type = type
		self.name = None
		self.index = len(self.all_signals)
		self.all_signals.append(self)

		self.func = None
		self.driving_signals = None
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
		self.clock = clock
		if args:
			self.driving_signals = list(args)

	def __str__(self):
		return str(self.current_val)

	def __int__(self):
		return int(self.current_val, 2)

	def __nonzero__(self):
		return str(self.current_val) == "1"

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


comparator_count = 1
class CompareOperation:
	derived_count = 1

	def __init__(self, nodes, comparators):
		self.nodes = nodes
		self.comparators = comparators
		global comparator_count
		self.result = Signal(1)
		self.result.name = "comparator_"+str(comparator_count)
		comparator_count += 1

	def __str__(self):
		node_pairs = [(str(self.nodes[x]), str(self.nodes[x+1])) for x in range(len(self.nodes)-1)]
		ast_to_vhdl = {ast.Eq: " = "}
		comparisons = [node_pairs[x][0] + ast_to_vhdl[type(self.comparators[x])] + node_pairs[x][1] for x in range(len(node_pairs))]
		return "\"1\" when " + " and ".join(comparisons) + " else \"0\";"


def to_string(new_val):
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


def to_list(args):
	if type(args) is list:
		return args
	elif type(args) is tuple:
		return list(*args)
	else:
		return [args]


def get_all_entity_signals(*nodes):
	unseen_signals = to_list(nodes)
	seen_signals = []
	while unseen_signals:
		current = unseen_signals.pop()
		seen_signals.append(current)
		if current.driving_signals:
			for drive_input in current.driving_signals:
				if isinstance(drive_input, Signal):
					if drive_input not in seen_signals:
						unseen_signals.append(drive_input)
	return seen_signals


def get_driving_signals(top_node, signal, compare_signals):
	all_input_signals = [x.id for x in top_node.body[0].args.args]
	driving_names = []
	for node in ast.walk(top_node):
		if isinstance(node, ast.If):
			for subnode in ast.walk(node.test):
				if isinstance(subnode, ast.Name):
					if subnode.id in all_input_signals:
						driving_names.append(subnode.id)
	driving_signals = []
	for signal_name in driving_names:
		if signal_name[:9] == "compare_":
			driving_signals.append(compare_signals[int(signal_name[9+len(signal.name):])-1])
		else:
			driving_signals.append(signal.driving_signals[all_input_signals.index(signal_name)])
	return driving_signals


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
		func_output = destination.func(*destination.driving_signals)
		if func_output not in lut.keys():
			lut[func_output] = [func_input_line]
		else:
			lut[func_output].append(func_input_line)
	return lut


def get_logic(driven, driving_signals):
	lut = get_lut(driven, driving_signals)
	text = "case(" + " & ".join([x.name for x in driving_signals]) + ") is\n"
	for each in lut.keys():
		if each != None:
			for input in lut[each]:
				text += "when \"" + "".join(input) + "\" => " + driven.name + " <= " + to_string(each) + ";\n"
	text += "when others => pass;\n"
	text += "end case;\n"
	return text


def node_replace(original, replace_dict):
	for node in ast.walk(original):
		if isinstance(node, ast.Name):
			if node.id in replace_dict.keys():
				node.id = replace_dict[node.id]


def replace_with_operator(node):
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


derived_count = 1
def optimize_compare_vals(top_node, signal):
	func_args = [x.id for x in top_node.body[0].args.args]
	replace_dict = dict([(func_args[x], signal.driving_signals[x].name) for x in range(len(func_args))])

	compare_signals = []
	compare_nodes = list(filter(lambda x: isinstance(x, ast.Compare), ast.walk(top_node)))
	for node in compare_nodes:
		compare_vals = copy.deepcopy([node.left] + node.comparators)
		for x in range(len(compare_vals)):
			node_replace(compare_vals[x], replace_dict)
			replace_with_operator(compare_vals[x])
			compare_vals[x] = eval(compile(ast.Expression(compare_vals[x]), filename="<ast>", mode="eval"))
		new_signal_id = len(compare_signals)+1
		new_signal_name = "compare_" + signal.name + "_" + str(new_signal_id)
		new_signal = Signal(1)
		new_signal.name= new_signal_name
		new_signal.drive(CompareOperation(compare_vals, node.ops))
		compare_signals.append(new_signal)
		signal.driving_signals.append(new_signal)
		node.left = ast.Call(func=ast.Name(id='int', ctx=ast.Load()), args=[ast.Name(id=new_signal_name, ctx=ast.Load())], keywords=[], starargs=None, kwargs=None)
		node.ops = [ast.Eq()]
		node.comparators = [ast.Num(n=1)]
		top_node.body[0].args.args.append(ast.Name(id=new_signal_name, ctx=ast.Param()))
	ast.fix_missing_locations(top_node)
	return compare_signals


def optimize_returns(top_node):
	return_nodes = list(filter(lambda x: isinstance(x, ast.Return), ast.walk(top_node)))
	for node in return_nodes:
		replace_with_operator(node)


def compare_logic(signal):
	return signal.name + " <= " + str(signal.func)


def ast_magic(signal):
	"""
	Takes in a driven signal
	Parses the driving function into an ast
	Find all ast.Compare, generates compare_signals, swaps comparisons for compare_signals
	Find all ast.Return, swaps int(), bool() and str() to to_int(), to_bool and to_str(), changing returns to BinOperators
	Fixes function namespace
	Saves new function
	Find and return all non-comparison, free LUT inputs

	:param signal: A driven Signal.
	:return: (compare_signals, lut)
	"""
	top_node = ast.parse(inspect.getsource(signal.func))
	print(ast.dump(top_node))
	compare_signals = optimize_compare_vals(top_node, signal)
	optimize_returns(top_node)
	exec(compile(top_node, filename="<ast>", mode="exec"))
	func_name = top_node.body[0].name
	signal.func = (eval(func_name))
	driving_signals = get_driving_signals(top_node, signal, compare_signals)
	return [compare_logic(x) for x in compare_signals], get_logic(signal, driving_signals)


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


def get_name(nodes):
	for each in nodes:
		try:
			each.name = ([k for k, v in globals().iteritems() if v is each][0])
		except:
			x = 1
			while True:
				if "signal_" + str(x) not in globals().keys():
					each.name = "signal_"+str(x)
					globals()["signal_"+str(x)] = each
					break
				x += 1


def generate_vhdl(code_globals, *nodes):
	for each in code_globals:
		if each not in globals().keys():
			globals()[each] = code_globals[each]
	entity_signals = get_all_entity_signals(nodes)
	get_name(entity_signals)
	text = generate_header(entity_signals)
	text += "architecture generated_arch of generated is\n\n"
	print("Header complete")
	for signal in entity_signals:
		if signal.type != "in":
			if signal.driving_signals:
				compares, original = ast_magic(signal)
				for each in compares:
					text += each + "\n"
				if signal.clock:
					text += "process(clock) is\n"
					text += "if rising_edge(clock) then\n"
				text += original
				if signal.clock:
					text += "end if;\n"
					text += "end process;\n"
			else:
				if signal.func:
					text += signal.name + " <= " + to_string(signal.func) + ";\n"
			print("Signal " + signal.name + " complete")
			text += "\n"
	text += "end generated_arch;"
	text = indent(text)
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
