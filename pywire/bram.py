from .component import Component
from .main import *
import math


class BRAM(Component):
	bram_count = 0

	def __init__(self, width, depth, a_write=True, a_read=True, b_write=False, b_read=False):
		Component.__init__(self)
		self.bram_count += 1
		self.id = str(self.bram_count)
		self.depth = depth
		self.width = width
		self.props = {"a_write":a_write, "a_read":a_read, "b_write":b_write, "b_read":b_read}
		self.a_address = Signal(int(math.ceil(math.log(depth, 2))), name="BRAM_" + self.id + "_a_address")
		if a_write:
			self.a_write_en = Signal(1, name="BRAM_" + self.id + "_a_write_en")
			self.a_data_in = Signal(width, name="BRAM_" + self.id + "_a_data_in")
		if a_read:
			self.a_data_out = Signal(width, name="BRAM_" + self.id + "_a_data_out")
		if b_write or b_read:
			self.b_address = Signal(int(math.ceil(math.log(depth, 2))), name="BRAM_" + self.id + "_b_address")
		if b_read:
			self.b_data_out = Signal(width, name="BRAM_" + self.id + "_b_data_out")
		if b_write:
			self.b_write_en = Signal(1, name="BRAM_" + self.id + "_b_write_en")
			self.b_data_in = Signal(width, name="BRAM_" + self.id + "_b_data_in")

	def body(self):
		body_text = "process(clock) begin\n"
		body_text += "if rising_edge(clock) then\n"
		if self.props["a_read"]:
			body_text += self.a_data_out.name + " <= RAM_" + self.id + "(conv_integer(" + self.a_address.name + "));\n"
		if self.props["a_write"]:
			body_text += "if " + self.a_write_en.name + ' = "1" then\n'
			body_text += "RAM_" + self.id + "(conv_integer(" + self.a_address.name + ")) := " + self.a_data_in.name + ";\n"
			body_text += "end if;\n"
		body_text += "end if;\nend process;\n"

		if self.props["b_read"] or self.props["b_write"]:
			body_text = "process(clock) begin\n"
			body_text += "if rising_edge(clock) then\n"
			if self.props["b_read"]:
				body_text += self.b_data_out.name + " <= RAM_" + self.id + "(conv_integer(" + self.b_address.name + "));\n"
			if self.props["b_write"]:
				body_text += "if " + self.b_write_en.name + ' = "1" then\n'
				body_text += "RAM_" + self.id + "(conv_integer(" + self.b_address.name + ")) := " + self.b_data_in.name + ";\n"
				body_text += "end if;\n"
		return body_text

	def header(self):
		text = "type ram_type_" + str(self.id) + " is array (" + str(self.depth-1) + " downto 0) of std_logic_vector(" + str(self.width-1) + " downto 0);\n"
		return text + "shared variable RAM_" + str(self.id) + " : ram_type_" + str(self.id) + " := (others => (others => '0'));"
