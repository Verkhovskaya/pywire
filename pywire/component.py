from .signal import Signal
import math


class Component:
    all_components = []

    def __init__(self):
        self.all_components.append(self)

    def body(self):
        return ""  # Can be overwritten in Component sub-class

    def header(self):
        return ""  # Can be overwritten in Component sub-class


class FromText(Component):
    def __init__(self, links, text):
        Component.__init__(self)
        self.links = links
        flat_text = text\
            .replace("\n", " ")\
            .replace("\t", "")\
            .replace(")", " ) ")\
            .replace("(", " ( ")\
            .replace(";", " ; ")\
            .split(" ")
        while '' in flat_text:
            flat_text.remove('')

        self.name = flat_text[flat_text.index("entity")+1]
        if not self.name:
            raise Exception("Could not find entity name")

        self.signals = {}
        all_in_indexes = [i for i, x in enumerate(flat_text) if x == "in"]
        all_out_indexes = [i for i, x in enumerate(flat_text) if x == "out"]
        for x in all_in_indexes + all_out_indexes:
            signal_name = flat_text[x-2]
            try:
                assert signal_name not in self.signals.keys()
            except AssertionError:
                raise AssertionError("Signal '" + signal_name + "' defined already defined")

            signal_io = flat_text[x]
            try:
                assert signal_io in ["in", "out"]
            except AssertionError:
                raise AssertionError("Invalid signal io direction: '" + signal_io + "'. Expecting 'in' or 'out'")

            vector_type = flat_text[x+1]
            if vector_type == "std_logic_vector":
                if flat_text[x+4] == "to":
                    start = flat_text[x+3]
                    end = flat_text[x+5]
                elif flat_text[x+4] == "downto":
                    start = flat_text[x+5]
                    end = flat_text[x+3]
                else:
                    raise Exception("Unknown command '" + flat_text[x+4] + "'. expected 'to' or 'downto'")

                try:
                    signal_size = int(end) - int(start) + 1
                    assert isinstance(signal_size, int)
                except TypeError:
                    raise Exception("Invalid range " + start + " " + flat_text[x+4] + " " + end)
            else:
                raise Exception("Invalid vector type: '" + vector_type + "'. Expecting std_logic_vector")

            self.signals[signal_name] = {"size": signal_size, "io": signal_io}

        header_text = " ".join(
            flat_text[flat_text.index("port")+2:flat_text.index("end")])\
            .replace(" ; ", ";\n")\
            .replace("is ", "is\n")\
            .replace("( ", "(")\
            .replace(" )", ")")\
            .replace(" ;",";")

        self.header_text = "component " + self.name + " is\n" + header_text + "\nend component;"

    def body(self):
        text = ""
        text += "COMPONENT_" + str(len(Component.all_components)) + " : " + self.name + "\nport map (\n"
        for x in self.links.keys():
            if self.signals[x]["size"] == 0:
                text += x + " => " + self.links[x].name + "(0);\n"
            else:
                text += x + " => " + self.links[x].name + ";\n"
        text += "clock => clock;\n"
        text += ");"
        return text

    def header(self):
        return self.header_text


class BRAM(Component):
    bram_count = 0

    @staticmethod
    def identity(x):
        return x

    def __init__(self, links, width, depth, a_write=True, a_read=True, b_write=False, b_read=False):
        Component.__init__(self)
        self.links = links
        self.bram_count += 1
        self.id = str(self.bram_count)
        self.depth = depth
        self.width = width
        self.props = {"a_write": a_write, "a_read": a_read, "b_write": b_write, "b_read": b_read}
        self.a_address = Signal(int(math.ceil(math.log(depth, 2))))
        self.a_address.name = "BRAM_" + self.id + "_a_address"
        self.a_address.drive(BRAM.identity, links["a_address"], clock=False)
        if a_write:
            self.a_write_en = Signal(1)
            self.a_write_en.name = "BRAM_" + self.id + "_a_write_en"
            self.a_write_en.drive(BRAM.identity, links["a_write_en"], clock=False)
            self.a_data_in = Signal(width)
            self.a_data_in.name = "BRAM_" + self.id + "_a_data_in"
            self.a_data_in.drive(BRAM.identity, links["a_data_in"], clock=False)
        if a_read:
            self.a_data_out = Signal(width)
            self.a_data_out.name= "BRAM_" + self.id + "_a_data_out"
            links["a_data_out"].drive(BRAM.identity, self.a_data_out, clock=False)
        if b_write or b_read:
            self.b_address = Signal(int(math.ceil(math.log(depth, 2))))
            self.b_address.name = "BRAM_" + self.id + "_b_address"
            self.b_address.drive(BRAM.identity, links["b_address"], clock=False)
        if b_read:
            self.b_data_out = Signal(width)
            self.b_data_out.name = "BRAM_" + self.id + "_b_data_out"
            links["b_data_out"].drive(BRAM.identity, self.b_data_out, clock=False)
        if b_write:
            self.b_write_en = Signal(1)
            self.b_write_en.name = "BRAM_" + self.id + "_b_write_en"
            self.b_write_en.drive(BRAM.identity, links["b_write_en"], clock=False)
            self.b_data_in = Signal(width)
            self.b_data_in.name = "BRAM_" + self.id + "_b_data_in"
            self.b_data_in.drive(BRAM.identity, links["b_data_in"], clock=False)

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
