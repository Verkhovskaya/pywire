import ast
import inspect
import copy
import logging
import math


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
		if name is not None:
			globals()[name] = self
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
		if self.name:
			return self.name
		else:
			return "BROKEN?"

	def __add__(self, other):
		return str(self) + " + " + str(other)

	def down(self, num):
		new_name = self.name + "_1d"
		if new_name not in globals().keys():
			new_signal = Signal(1).drive(self)
			new_signal.name = new_name
			globals()[new_name] = new_signal
		return new_name


def __generate_header():
	i_signals = list(filter(lambda x: x.io == "in", Signal.all_signals))
	o_signals = list(filter(lambda x: x.io == "out", Signal.all_signals))

	io_texts = [x.name + " : " + x.io + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in i_signals]
	io_texts += [x.name + " : " + x.io + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in o_signals]
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


def compare_node_to_string(node, signal, top_node):
	func_args = [x.id for x in top_node.body[0].args.args]
	replace_dict = dict([(func_args[x], signal.driving_signals[x].name) for x in range(len(func_args))])
	compare_vals = copy.deepcopy([node.left] + node.comparators)
	for x in range(len(compare_vals)):
		replace_args_with_signals(compare_vals[x], replace_dict)
		compare_vals[x] = str(eval(compile(ast.Expression(compare_vals[x]), filename="<ast>", mode="eval")))
	node_pairs = [(compare_vals[x], compare_vals[x+1]) for x in range(len(compare_vals)-1)]
	ast_to_vhdl = {ast.Eq: " = ", ast.Gt: " > ", ast.Lt: " < "}
	comparisons = [as_vhdl_string(node_pairs[x][0]) + ast_to_vhdl[type(node.ops[x])] + as_vhdl_string(node_pairs[x][1]) for x in range(len(node_pairs))]
	return '"1" when ' + ' and '.join(comparisons) + ' else "0"'


def __optimize_compare_vals(top_node, signal):
	compare_signals = []
	compare_nodes = list(filter(lambda x: isinstance(x, ast.Compare), ast.walk(top_node)))
	for node in compare_nodes:
		new_signal_name = "compare_" + signal.name + "_" + str(len(compare_signals)+1)
		new_signal = Signal(1, name=new_signal_name).drive(compare_node_to_string(node, signal, top_node), clock=False)
		compare_signals.append(new_signal)
		signal.driving_signals.append(new_signal)
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
		if first_word in ("entity", "port", "begin", "if", "case", "process", "else", "component"):
			level += 1
	return "\n".join(out_text)


def generate_vhdl(code_globals):
	all_signals = copy.copy(Signal.all_signals)
	for signal in all_signals:
		if signal.name is None:
			if signal in code_globals.values():
				signal.name = filter(lambda x: id(code_globals[x]) == id(signal), code_globals.keys())[0]
			else:
				signal.name = "unnamed_" + str(len(filter(signal.name[:8] == "unnamed_", Signal.all_signals)))
		if signal.io == "out":
			Signal(1, io="out", name=signal.name).drive(signal, clock=False)
			signal.name = signal.name + "_mask"
			signal.io = None
		globals()[signal.name] = signal
	arch_signal_text = ""
	body_text = ""
	for each in Import.all_imports:
		arch_signal_text += each.header() + "\n"
		body_text += each.body() + "\n"
	signals_done = []
	while True:
		unseen = list(set([x.name for x in Signal.all_signals]) - set([x.name for x in signals_done]))
		if not unseen:
			break
		signal = filter(lambda x: x.name == unseen[0], Signal.all_signals)[0]
		signals_done.append(signal)
		new_arch_text, new_body_text, sub_done = generate_signal_vhdl(signal)
		arch_signal_text += new_arch_text
		body_text += new_body_text
		signals_done += sub_done
	header = __generate_header()
	return __indent(header + "architecture generated_arch of generated_top is\n\n" + arch_signal_text + "\nbegin\n\n" + body_text + "end generated_arch;")


def generate_signal_vhdl(signal):
	arch_text = ""
	body_text = ""
	sub_generated = []
	if signal.io != "in":
		if callable(signal.func):
			new_signals, logic_text = __ast_magic(signal)
			sub_generated += new_signals
			for each in new_signals:
				body_text += generate_signal_vhdl(each)[1] + "\n"
			if signal.clock:
				body_text += "process(clock) begin\n"
				body_text += "if rising_edge(clock) then\n"
			body_text += logic_text
			if signal.clock:
				body_text += "end if;\n"
				body_text += "end process;\n"
		elif signal.func is not None:
			if signal.clock:
				body_text += "process(clock) begin\n"
				body_text += "if rising_edge(clock) then\n"
			body_text += signal.name + " <= " + as_vhdl_string(signal.func, width=len(signal)) + ";\n"
			if signal.clock:
				body_text += "end if;\n"
				body_text += "end process;\n"
		logging.log(logging.INFO, "Signal " + signal.name + " complete")
		body_text += "\n"
	for each in [signal] + sub_generated:
		if each.io not in ["in", "out"]:
			arch_text = "signal " + each.name + " : std_logic_vector(0 to " + str(each.size-1) + ");\n"
	return arch_text, body_text, sub_generated


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


class Import:
	all_imports = []

	def __init__(self):
		self.all_components.append(self)
		self.links = []

	def instance(self, links):
		self.links.append(links)

	def body(self):
		pass  # Should be overwritten in Component sub-class

	def header(self):
		pass # Should be overwritten in Component sub-class


class FromPath(Import):
	def __init__(self, path):
		Import.__init__(self)
		read_file = open(path)
		flat_text = read_file.read().replace("\n", " ").replace("\t", "").replace(")", " ) ").replace("(", " ( ").replace(";", " ; ").split(" ")
		while '' in flat_text:
			flat_text.remove('')
		if "entity" not in flat_text:
			raise Exception("Could not find entity name")
		self.name = flat_text[flat_text.index("entity")+1]
		self.signals = {}
		all_in_indexes = [i for i, x in enumerate(flat_text) if x == "in"]
		all_out_indexes = [i for i, x in enumerate(flat_text) if x == "out"]
		for x in all_in_indexes + all_out_indexes:
			signal_name = flat_text[x-2]
			signal_io = flat_text[x]
			vector_type = flat_text[x+1]
			if vector_type == "std_logic":
				signal_size = 0
			elif vector_type == "std_logic_vector":
				if flat_text[x+4] == "to":
					signal_size = int(flat_text[x+5])-int(flat_text[x+3])+1
				else:
					signal_size = int(flat_text[x+3])-int(flat_text[x+5])+1
			else:
				raise Exception("Only std_logic and std_logic_vector are supported by Valerian as IO types")
			self.signals[signal_name] = {"size": signal_size, "io": signal_io}
		header_text = " ".join(flat_text[flat_text.index("port")+2:flat_text.index("end")]).replace(" ; ", ";\n").replace("is ", "is\n").replace("( ", "(").replace(" )", ")").replace(" ;",";")
		self.header_text = "component " + self.name + " is\n" + header_text + "\nend component;"

	def body(self):
		text = ""
		text += (self.name + "_INSTANCE_" + str(i)).upper() + " : " + self.name + "\nport map (\n"
		for x in self.link.keys():
			if self.link[x]["type"] == "std_logic_vector":
				text += x + " => " + self.link[x].name + ";\n"
			else:
				text += x + " => " + self.link[x].name + "(0);\n"

		text += "\n".join([x + " => " + self.link[x].name for x in self.link.keys()]) + ");\n"
		return text

	def header(self):
		return self.header_text


class BRAM(Import):
	bram_count = 0

	def __init__(self, depth, width, port_a_write, port_a_read, port_b_write=False, port_b_read=False):
		self.bram_count += 1
		self.id = str(self.bram_count)
		address_a = Signal(width, name="BRAM_" + self.id + "_address_a")
		if port_a_write:
			write_en_a = Signal(1, name="BRAM_" + self.id + "_write_en_a")
			data_in_a = Signal(width, name="BRAM_" + self.id + "_data_in_a")
		if port_a_read:
			data_out_a = Signal(width, name="BRAM_" + self.id + "_data_out_a")
		if port_b_write or port_b_read:
			address_b = Signal(width, name="BRAM_" + self.id + "_address_b")
		if port_b_read:
			data_out_b = Signal(width, name="BRAM_" + self.id + "_data_out_b")
		if port_b_write:
			write_en_b = Signal(1, name="BRAM_" + self.id + "_write_en_b")
			data_in_b = Signal(width, name="BRAM_" + self.id + "_data_in_b")

		self.header = "type ram_type_" + str(self.id) + " is array (" + str(depth-1) + " downto 0) of std_logic_vector(" + str(width-1) + " downto 0);\n"
		self.header += "shared variable RAM_" + str(self.id) + " : ram_type := (others => (others => '0'));"

		body_text = "process(clock) begin\n"
		body_text += "if rising_edge(clock) then\n"
		if port_a_read:
			body_text += data_out_a.name + " <= RAM_" + self.id + "(conv_integer(" + address_a.name + "));\n"
		if port_a_write:
			body_text += "if " + write_en_a.name + ' = "1" then\n'
			body_text += "RAM_" + self.id + "(conv_integer(" + address_a.name + ")) := " + data_in_a.name + ";\n"
			body_text += "end if;\n"
		body_text += "end if;\nend process;\n"

		if port_b_read or port_b_write:
			body_text = "process(clock) begin\n"
			body_text += "if rising_edge(clock) then\n"
			if port_b_read:
				body_text += data_out_b.name + " <= RAM_" + self.id + "(conv_integer(" + address_b.name + "));\n"
			if port_b_write:
				body_text += "if " + write_en_b.name + ' = "1" then\n'
				body_text += "RAM_" + self.id + "(conv_integer(" + address_b.name + ")) := " + data_in_b.name + ";\n"
				body_text += "end if;\n"
			body_text += "end if;\nend process;\n"
		self.body_text = body_text

	def body(self):
		return self.body_text

	def header(self):
		if self.id == "1":
			return self.header
		else:
			return ""
