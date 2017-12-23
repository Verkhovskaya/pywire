import os
import datetime
import subprocess

from signal_v2 import Signal

def generate_vhdl(*signals):
	text = "library ieee;"
	text += "\nuse ieee.std_logic_1164.all;"
	text += "\n\nentity generated_top is"
	text += "\nport ("
	text += "\n    clock : in std_logic"
	text += "".join(map(lambda x: ";\n" + port_vhdl(x), filter(lambda x: x.io, signals)))
	text += "\n);"
	text += "\nend entity;"
	text += "\n\narchitecture generated_logic of generated_top is\n"
	for each in signals:
		text += signal_declaration_vhdl(each) + "\n"
	text += "\n\nbegin\n"
	for each in signals:
		text += logic_vhdl(each) + "\n"
	text += "\n\nend generated_logic;"

	return indent(text)


def port_vhdl(signal):
	if type(signal.io) is str:
		return signal.name + " : " + signal.io + " std_logic_vector(0 to " + str(signal.size-1) + ")"


def signal_declaration_vhdl(signal):
	return signal.name + " : std_logic_vector(0 to " + str(signal.size-1) + ");"

def logic_tuple_to_string(my_tuple):
	expanded = list(my_tuple)
	if type(expanded[1]) == tuple:
		expanded[1] = logic_tuple_to_string(my_tuple[1])
	elif isinstance(expanded[1], Signal):
		expanded[1] = expanded[1].name
	if type(expanded[2]) == tuple:
		expanded[2] = logic_tuple_to_string(my_tuple[1])
	elif isinstance(expanded[2], Signal):
		expanded[1] = expanded[2].name
	return str(expanded[1]) + " " + str(expanded[0]) + " " + str(expanded[2])


def to_assign(something):
		if isinstance(something, Signal):
			return something.name
		elif type(something) == str:
			return something
		elif type(something) == tuple:
			return logic_tuple_to_string(something)
		else:
			return "ERROR, INVALID TYPE " + str(something)


def case_vhdl(signal):
	text = "case(" + " & ".join([x.name for x in signal.uses_signals]) + ") is\n"
	results = signal.driver_simple.keys()
	for result in results:
		parse_result = to_assign(result)
		for case in signal.driver_simple[result]:
			text += "".join(case) + " => " + signal.name + " <= " + parse_result + ";\n"
	text += "end case;"
	return text


def logic_vhdl(signal):
	if not signal.driver:
		print("Signal " + signal.name + " is undriven")
		return ""
	elif type(signal.driver) == str:
		return signal.name + " <= \"" + signal.driver + "\";"
	elif type(signal.driver) == tuple:
		return signal.name + " <= " + signal.driver[1].name + " " + signal.driver[0] + " " + signal.driver[2].name + ";"
	elif type(signal.driver) == Signal:
		return signal.name + " <= " + signal.driver.name
	else:
		return case_vhdl(signal)


def indent(in_text):
	level = 0
	in_text = filter(lambda x: x != "", in_text.split("\n"))
	out_text = []
	for each in in_text:
		vertical_spacing = [0, 0]  # Default
		each = each.strip()
		if " " in each:
			first_word = each[:each.replace("(", " (").index(" ")]
		else:
			first_word = each
		if first_word in ("architecture", "process", "entity"):  # Add vertical spacing before
			vertical_spacing[0] = 1
		if first_word in [");", "end", "begin"]:
			level -= 1
		out_text.append("\n"*vertical_spacing[0] + "    "*level + each + "\n"*vertical_spacing[1])
		if first_word in ("entity", "port", "architecture", "begin", "if", "case", "process"):
			level += 1
	return "\n".join(out_text)


def generate_ucf(entity):
	text = 'NET "clock" TNM_NET = clock;'
	text += '\nTIMESPEC TS_clk = PERIOD "clock" ' + str(entity.frequency) + ' MHz HIGH 50%;'
	text += "\n"
	for each in entity.ports:
		text += '\nNET "' + each.name + '" LOC = ' + each.name.upper() + ' | IOSTANDARD = LVTTL;'
	return text


def generate_bin(entity, notes=None):
	base_address = "/Users/2017-A/Dropbox/fpga/fpga_builds"
	timestamp = str(datetime.datetime.now()).replace(" ", "_").replace(":", "_").replace("-", "_")[:-7]
	directory = base_address + "/" + timestamp
	os.mkdir(directory)
	os.chdir(directory)
	os.mkdir("src")
	top = open(directory + "/src/generated_top.vhd", "w")
	top.write(entity.generate_vhdl())
	top.close()
	if notes:
		notes_file = open(directory + "/build_notes.txt", "w")
		notes_file.write(notes)
	ucf = open(directory + "/src/generated_top.ucf", "w")
	ucf.write(entity.generate_ucf())
	ucf.close()
	build_files = ["generated_top.vhd", "generated_top.ucf"]
	top_file = "generated_top"
	args = timestamp + " " + top_file + " " + " ".join(build_files)
	print("bash /Users/2017-A/Dropbox/tools/fpga_builds/build_fpga.sh " + args)
	subprocess.call("bash /Users/2017-A/Dropbox/fpga/fpga_builds/build_fpga.sh " + args, shell=True)
