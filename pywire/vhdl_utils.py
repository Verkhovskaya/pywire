def as_string(val, width=1):
    if type(val) is str:
        if len(list(filter(lambda x: x not in ["0", "1"], val))) == 0:
            return '"' + val + '"'
    if type(val) is int:
        return '"' + bin(val)[2:].zfill(width) + '"'
    return str(val)


def generate_header(entity_name, entity_signals):
    i_signals = list(filter(lambda x: x.io == "in", entity_signals))
    o_signals = list(filter(lambda x: x.io == "out", entity_signals))

    io_texts = [x.name + " : " + x.io + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in i_signals]
    io_texts += [x.name + " : " + x.io + " std_logic_vector(0 to " + str(x.size-1) + ")" for x in o_signals]
    text = "library ieee;\n"
    text += "use ieee.std_logic_1164.all;\n"
    text += "use ieee.numeric_std.all;\n\n"
    text += "entity " + entity_name + " is\n"
    text += "port(\n"
    text += ";\n".join(["clock : in std_logic"]+io_texts)
    text += ");\n"
    text += "end entity;\n\n"
    return text


def logic_to_case_text(driven_signal, driving_signals):
    lut = logic_to_case_text(driven_signal, driving_signals)
    text = "case(" + " & ".join([x.name for x in driving_signals]) + ") is\n"
    for each in lut.keys():
        if not each:
            for input_signal in lut[each]:
                text += "when \"" + "".join(input_signal) + "\" => " + driven_signal.name + " <= " + as_string(each) + ";\n"
    text += "when others => null;\n"
    text += "end case;\n"
    return text


def indent_text(text):
    level = 0
    out_text = []
    for each in text.split("\n"):
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


def generate_timing_text(entity_signals, frequency, clock_pin):
    text = 'NET "clock" TNM_NET = clock;\n'
    text += 'TIMESPEC TS_clk = PERIOD "clock" ' + str(frequency/1000000.0) + ' MHz HIGH 50%;\n'
    text += 'NET "clock" LOC = ' + clock_pin + ' | IOSTANDARD = LVTTL;\n'
    for signal in entity_signals:
        if signal.port:
            for index in range(len(signal.port)):
                text += 'NET "' + signal.name + '<' + str(index) + '>" LOC = '\
                        + signal.port[index] + ' | IOSTANDARD = LVTTL;\n'
    return text


def join_code(header, entity_name, component_headers, body_text):
    return indent_text(header + "architecture " + entity_name + "_arch of " + entity_name + " is\n\n"\
                        + component_headers + "\nbegin\n\n" + body_text + "end " + entity_name + "_arch;")