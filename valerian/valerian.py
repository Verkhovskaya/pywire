import ast
import inspect
import copy
import logging
import math


"""
General code structure:

Signal class (Data storage for library access)
Several Operator classes

"""

def to_list(args):
	if type(args) is list:
		return args
	elif type(args) is tuple:
		return list(args)
	else:
		return [args]


def replace_args_with_signals(original, replace_dict):
	for node in ast.walk(original):
		if isinstance(node, ast.Name):
			if node.id in replace_dict.keys():
				node.id = replace_dict[node.id]


def as_vhdl_string(val, width=1):
	if type(val) is str:
		if len(filter(lambda x: x not in ["0", "1"], val)) == 0:
			return '"' + val + '"'
	if type(val) is int:
		return '"' + bin(val)[2:].zfill(width) + '"'
	return str(val)

class Signal:
	all_signals = []

	def __init__(self, bit_size, io=None, port=None, name=None):
		self.size = int(bit_size)
		self.io = io
		self.name = name
		self.index = len(self.all_signals)
		self.all_signals.append(self)
		if port is not None:
			if type(port) is tuple or type(port) is list:
				self.port = port
			else:
				self.port = [port]
		else:
			self.port = None

		self.func = None
		self.driving_signals = None
		self.clock = None

		self.current_val = 0

	def drive(self, func, args=None, clock=True):
		self.func = func
		self.clock = clock
		if args != None:
			self.driving_signals = to_list(args)
		return self

	def __len__(self):
		return self.size

	def __eq__(self, other):
		return as_vhdl_string(self) + " = " + as_vhdl_string(other)

	def __trunc__(self):
		return self.current_val

	def __str__(self):
		return self.name

	def __add__(self, other):
		return str(self) + " + " + str(other)

	def down(self, num):
		new_name = self.name + "_1d"
		if new_name not in globals().keys():
			new_signal = Signal(1).drive(self)
			new_signal.name = new_name
			globals()[new_name] = new_signal
		return new_name


comparator_count = 1
class CompareOperation:
	derived_count = 1

	def __init__(self, node, signal, top_node):
		func_args = [x.id for x in top_node.body[0].args.args]
		replace_dict = dict([(func_args[x], signal.driving_signals[x].name) for x in range(len(func_args))])
		compare_vals = copy.deepcopy([node.left] + node.comparators)
		for x in range(len(compare_vals)):
			replace_args_with_signals(compare_vals[x], replace_dict)
			compare_vals[x] = eval(compile(ast.Expression(compare_vals[x]), filename="<ast>", mode="eval"))
		self.nodes = compare_vals
		self.comparators = node.ops
		global comparator_count
		self.result = Signal(1)
		self.result.name = "comparator_"+str(comparator_count)
		comparator_count += 1

	def __str__(self):
		self.nodes = [str(x) for x in self.nodes]
		node_pairs = [(str(self.nodes[x]), str(self.nodes[x+1])) for x in range(len(self.nodes)-1)]
		ast_to_vhdl = {ast.Eq: " = ", ast.Gt: " > ", ast.Lt: " < "}
		comparisons = [as_vhdl_string(node_pairs[x][0]) + ast_to_vhdl[type(self.comparators[x])] + as_vhdl_string(node_pairs[x][1]) for x in range(len(node_pairs))]
		return '"1" when ' + ' and '.join(comparisons) + ' else "0"'


def __generate_header(signal_names):
	signals = [globals()[x] for x in signal_names]
	i_signals = list(filter(lambda x: x.io == "in", signals))
	o_signals = list(filter(lambda x: x.io == "out", signals))

	io_texts = [x.name + " : " + x.io + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in i_signals]
	io_texts += [x.name[:-5] + " : " + x.io + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in o_signals]
	text = "library ieee;\n"
	text += "use ieee.std_logic_1164.all;\n"
	text += "use ieee.std_logic_unsigned.all;\n\n"
	text += "entity generated_top is\n"
	text += "port(\n"
	text += ";\n".join(["clock : in std_logic"]+io_texts)
	text += ");\n"
	text += "end entity;\n\n"
	return text


def __get_driving_signals(top_node, signal, compare_signals, get_all):
	all_input_signals = [x.id for x in top_node.body[0].args.args]
	if get_all:
		return [signal.driving_signals[all_input_signals.index(x)] for x in all_input_signals]
	driving_names = []
	for node in ast.walk(top_node):
		if isinstance(node, ast.If):
			for subnode in ast.walk(node.test):
				if isinstance(subnode, ast.Name):
					if subnode.id in all_input_signals and subnode.id not in driving_names:
						driving_names.append(subnode.id)
	driving_signals = []
	for signal_name in driving_names:
		if signal_name[:9] == "compare_":
			driving_signals.append(compare_signals[int(signal_name[9+len(signal.name):])-1])
		else:
			driving_signals.append(signal.driving_signals[all_input_signals.index(signal_name)])
	return driving_signals


def __match_widths(some_string, some_object):
	ret = []
	for each in some_object:
		ret.append(some_string[:len(each)])
		some_string = some_string[len(each):]
	return ret


def __get_lut(destination, driving_signals):
	total_width = sum([len(x) for x in driving_signals])
	lut = {}
	for i in range(2 ** total_width):
		func_input_line = __match_widths(bin(i)[2:].zfill(total_width), driving_signals)
		for j in range(len(driving_signals)):
			driving_signals[j].current_val = int(func_input_line[j], 2)
		func_output = destination.func(*destination.driving_signals)
		if type(func_output) is bool:
			func_output = {True: "1", False: "0"}[func_output]
		if func_output != None:
			func_output = as_vhdl_string(func_output, width=len(destination))
			if str(func_output) not in lut.keys():
				lut[str(func_output)] = [func_input_line]
			else:
				lut[str(func_output)].append(func_input_line)
	return lut


def __get_logic(driven, driving_signals):
	lut = __get_lut(driven, driving_signals)
	text = "case(" + " & ".join([x.name for x in driving_signals]) + ") is\n"
	for each in lut.keys():
		if each != None:
			for input in lut[each]:
				text += "when \"" + "".join(input) + "\" => " + driven.name + " <= " + as_vhdl_string(each) + ";\n"
	text += "when others => null;\n"
	text += "end case;\n"
	return text



derived_count = 1
def __optimize_compare_vals(top_node, signal):
	compare_signals = []
	compare_nodes = list(filter(lambda x: isinstance(x, ast.Compare), ast.walk(top_node)))
	for node in compare_nodes:
		new_signal_id = len(compare_signals)+1
		new_signal_name = "compare_" + signal.name + "_" + str(new_signal_id)
		new_signal = Signal(1).drive(CompareOperation(node, signal, top_node))
		new_signal.name = new_signal_name
		globals()[new_signal.name] = new_signal
		compare_signals.append(new_signal)
		signal.driving_signals.append(new_signal)
		global generated_signals
		generated_signals.append(new_signal_name)
		node.left = ast.Call(func=ast.Name(id='int', ctx=ast.Load()), args=[ast.Name(id=new_signal_name, ctx=ast.Load())], keywords=[], starargs=None, kwargs=None)
		node.ops = [ast.Eq()]
		node.comparators = [ast.Num(n=1)]
		top_node.body[0].args.args.append(ast.Name(id=new_signal_name, ctx=ast.Param()))
	ast.fix_missing_locations(top_node)
	return compare_signals


def __ast_magic(signal):
	"""
	Takes in a driven signal
	Parses the driving function into an ast
	Find all ast.Compare, generates compare_signals, swaps comparisons for compare_signals
	Fixes function namespace
	Saves new function
	Find and return all non-comparison, free LUT inputs

	:param signal: A driven Signal.
	:return: (compare_signals, lut)
	"""
	top_node = ast.parse(inspect.getsource(signal.func))
	compare_signals = __optimize_compare_vals(top_node, signal)
	exec(compile(top_node, filename="<ast>", mode="exec"))
	func_name = top_node.body[0].name
	signal.func = (eval(func_name))
	if isinstance(top_node.body[0].body[0], ast.Return):
		if isinstance(top_node.body[0].body[0].value, ast.Compare):
			compare_val = CompareOperation(top_node.body[0].body[0].value, signal, top_node)
			text = "if " + str(compare_val.nodes[0]) + ' = "1" then\n'
			text += signal.name + ' <= "1";\n'
			text += 'else\n'
			text += signal.name + ' <= "0";\n'
			text += 'end if;\n'
			return compare_signals, text
		else:
			func_args = [x.id for x in top_node.body[0].args.args]
			replace_dict = dict([(func_args[x], signal.driving_signals[x].name) for x in range(len(func_args))])
			return_func = copy.deepcopy(top_node.body[0].body[0].value)
			replace_args_with_signals(return_func, replace_dict)
			return_val = str(eval(compile(ast.Expression(return_func), filename="<ast>", mode="eval")))
			return compare_signals, signal.name + " <= " + as_vhdl_string(return_val, width=len(signal)) + ";\n"
	else:
		driving_signals = __get_driving_signals(top_node, signal, compare_signals, False)
		return compare_signals, __get_logic(signal, driving_signals)


def __indent(in_text):
	level = 0
	in_text = in_text.split("\n")
	out_text = []
	for each in in_text:
		each = each.strip()
		if " " in each:
			first_word = each[:each.replace("(", " (").index(" ")]
		else:
			first_word = each
		if first_word in [");", "end", "begin", "else"]:
			level -= 1
		out_text.append("    "*level + each)
		if first_word in ("entity", "port", "begin", "if", "case", "process", "else"):
			level += 1
	return "\n".join(out_text)


def generate_vhdl(code_globals):
	"""
	1. Finds all Signals in globals, sets their name
	- If the signal is an output, create a signal mask
	2. For each original or generated signal:
		Generate body and signal text
	3. generate header text
	return text
	:param code_globals: globals() of calling program
	:return: VHDL text
	"""

	global all_signals

	for each in code_globals:
		if isinstance(code_globals[each], Signal):
			signal = code_globals[each]
			if signal.io == "out":
				signal.name = each + "_mask"
				Signal(1, name=each).drive(signal, clock=False)
			else:
				signal.name = each
			globals()[signal.name] = signal
	signal_text = "architecture generated_arch of generated_top is\n\n"
	body_text = "\nbegin\n\n"
	global generated_signals
	generated_signals = []
	while True:
		all_signals = filter(lambda x: isinstance(globals()[x], Signal), globals().keys())
		unseen = list(set(all_signals) - set(generated_signals))
		if not unseen:
			break
		generated_signals.append(unseen[0])
		signal = globals()[unseen[0]]
		if signal.io not in ["in", "out"]:
			signal_text += "signal " + signal.name + " : std_logic_vector(0 to " + str(signal.size-1) + ");\n"
		if signal.io != "in":
			if signal.driving_signals:
				compares, original = __ast_magic(signal)
				for each in compares:
					body_text += each.name + " <= " + str(each.func) + ";\n"
					signal_text += "signal " + each.name + " : std_logic_vector(0 to " + str(each.size-1) + ");\n"
				if signal.clock:
					body_text += "process(clock) begin\n"
					body_text += "if rising_edge(clock) then\n"
				body_text += original
				if signal.clock:
					body_text += "end if;\n"
					body_text += "end process;\n"
			else:
				if signal.func != None:
					if signal.clock:
						body_text += "process(clock) begin\n"
						body_text += "if rising_edge(clock) then\n"
					body_text += signal.name + " <= " + as_vhdl_string(signal.func, width=len(signal)) + ";\n"
					if signal.clock:
						body_text += "end if;\n"
						body_text += "end process;\n"
			logging.log(logging.INFO, "Signal " + signal.name + " complete")
			body_text += "\n"
	body_text += "end generated_arch;"
	body_text = __indent(body_text)
	header = __generate_header(generated_signals)
	return header + signal_text + body_text


def generate_ucf(code_globals, frequency, clock_pin):
	entity_signals = []
	for each in code_globals:
		if isinstance(code_globals[each], Signal):
			signal = code_globals[each]
			globals()[each] = signal
			entity_signals.append(signal)
			signal.name = each
	text = 'NET "clock" TNM_NET = clock;\n'
	text += 'TIMESPEC TS_clk = PERIOD "clock" ' + str(frequency) + ' MHz HIGH 50%;\n'
	text += 'NET "clock" LOC = ' + clock_pin + ' | IOSTANDARD = LVTTL;\n'
	for signal in entity_signals:
		if signal.port:
			for x in range(len(signal.port)):
				text += 'NET "' + signal.name + '<' + str(x) + '>" LOC = ' + signal.port[x] + ' | IOSTANDARD = LVTTL;\n'
	return text
