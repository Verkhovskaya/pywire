import ast
from .component import Component
from .signal import Signal
from .vhdl_utils import generate_header, generate_timing_text, join_code
import copy


def __ast_magic(node, meta_info):
    if not node:
        return ""
    elif isinstance(node, ast.BoolOp):
        bool_ops = {ast.And: " and "}
        return bool_ops[type(node.op)].join(
            ["(" + __ast_magic(x, meta_info) + ")" for x in node.values])
    elif isinstance(node, ast.BinOp):
        math_ops = {ast.Add: "+", ast.Div: "/", ast.Sub: "-", ast.Mult: "*"}
        bin_ops = {ast.And: "and", ast.BitAnd: "and",
                   ast.BitOr: "or", ast.BitXor: "xor",
                   ast.Or: "or"}
        if isinstance(node.op, ast.Pow):
            return str(node.left.n**node.right.n)
        elif type(node.op) in bin_ops:
            return __ast_magic(node.left, meta_info) + " " +\
                   bin_ops[type(node.op)] + " "\
                   + __ast_magic(node.right, meta_info)
        elif type(node.op) in math_ops:
            meta_info_new = copy.copy(meta_info)
            meta_info_new["signal_to_num"] = True
            return __ast_magic(node.left, meta_info_new) + " " +\
                   math_ops[type(node.op)] + " "\
                   + __ast_magic(node.right, meta_info_new)
        else:
            raise Exception("Unrecognized binary operation: " + str(node.op) +
                            " of type " + str(type(node.op)))
    elif isinstance(node, ast.Name):
        signal_ref = meta_info["top_signal"].driving_signals[
            meta_info["function_args"].index(node.id)]
        return signal_ref.name
    elif isinstance(node, ast.Num):
        if isinstance(meta_info["top_signal"].signed, bool):
            return str(node.n)
        else:
            return '"' + bin(node.n)[2:] + '"'
    elif isinstance(node, ast.Return):
        return meta_info["top_signal"].name + " <= " +\
               __ast_magic(node.value, meta_info) + ";"
    elif isinstance(node, ast.If):
        if_text = __ast_magic(node.test, meta_info)
        if isinstance(node.test, ast.Name):
            if_text = "(" + if_text + '(0 to 0) = "1")'
        if node.orelse:
            else_text = __ast_magic(node.orelse, meta_info)
            if isinstance(node.orelse, ast.Name):
                else_text = "(" + if_text + '(0 to 0) = "1")'
            return "if " + if_text + " then\n" +\
                   "\n".join([__ast_magic(x, meta_info) for x in node.body]) +\
                   "\nelse\n" + else_text + "\nend if;"
        else:
            return "if " + if_text + " then\n" +\
                   "\n".join([__ast_magic(x, meta_info) for x in node.body]) +\
                   "\nend if;"
    elif isinstance(node, ast.Compare):
        text = __ast_magic(node.left, meta_info)
        for i in range(len(node.ops)):
            text += " " + __ast_magic(node.ops[i], meta_info) + " " +\
                    __ast_magic(node.comparators[i], meta_info)
        return text
    elif isinstance(node, ast.Gt):
        return ">"
    elif isinstance(node, ast.Lt):
        return "<"
    elif isinstance(node, ast.Eq):
        return "="
    elif isinstance(node, list):
        return "\n".join([__ast_magic(line, meta_info) for line in node])
    elif isinstance(node, ast.UnaryOp):
        unary_ops = {ast.Not: "-"}
        return unary_ops[type(node.op)] + " " + __ast_magic(node.operand, meta_info)
    elif isinstance(node, ast.NameConstant):
        if isinstance(node.value, bool):
            if node.value and meta_info["signal_to_num"]:
                return "1"*len(meta_info["top_signal"])
            elif node.value and not meta_info["signal_to_num"]:
                return '"' + '1'*len(meta_info["top_signal"]) + '"'
            elif not node.value and meta_info["signal_to_num"]:
                return "0"*len(meta_info["top_signal"])
            elif not node.value and not meta_info["signal_to_num"]:
                return '"' + '0'*len(meta_info["top_signal"]) + '"'
        else:
            raise Exception("Unsupported ast.nameConstant " + str(node.value))
    else:
        raise Exception("The " + str(type(node)) + " node is not yet supported."
                                            "Details: \n" + str(node) + ", " + str(node.__dict__))


def __replace_names_with_signals(original, replace_dict):
    for node in ast.walk(original):
        if isinstance(node, ast.Name):
            if node.id in replace_dict.keys():
                node.id = replace_dict[node.id]


def rename_signals(code_globals):
    for signal in Signal.all_signals:
        if signal in code_globals.values():
            signal_names = list(filter(lambda x: id(code_globals[x]) == id(signal), code_globals.keys()))
            if signal_names:
                signal.name = signal_names[0]
            assert isinstance(signal.name, str)
        globals()[signal.name] = signal


def generate_vhdl(name="generated_top"):
    header_text = "\n".join([each.header() for each in Component.all_components])
    body_text = "\n".join([each.body() for each in Component.all_components])

    signals_done = []
    while True:
        unseen = list(set([x.name for x in Signal.all_signals]) - set([x.name for x in signals_done]))
        if not unseen:
            break
        signal = list(filter(lambda x: x.name == unseen[0], Signal.all_signals))[0]
        if signal.driving_logic:
            new_header_text, new_body_text = generate_signal_text(signal)
            header_text += new_header_text
            body_text += new_body_text
        elif signal.io != "in":
            print("Signal " + signal.name + " is not driven by anything")
        signals_done.append(signal)
    header = generate_header(name, Signal.all_signals)
    return join_code(header, name, header_text, body_text)


def generate_signal_text(signal):
    header_text = ""
    body_text = ""
    if signal.io != "in":
        if signal.clock:
            body_text += "process(clock) begin\n"
            body_text += "if rising_edge(clock) then\n"
        top_node = signal.driving_logic
        try:
            assert len(top_node.body) == 1
            assert isinstance(top_node.body[0], ast.FunctionDef)
        except AssertionError:
            raise Exception("Function ast is not a function?")
        function_arg_names = [x.arg for x in top_node.body[0].args.args]
        body_text += "".join([__ast_magic(x, {"function_args": function_arg_names,
                                              "top_signal": signal,
                                              "signal_to_num": False})+"\n" for x in top_node.body[0].body])
        if signal.clock:
            body_text += "end if;\n"
            body_text += "end process;\n"

    print("Signal " + signal.name + " complete")

    body_text += "\n"
    for each in [signal]:
        if each.io not in ["in", "out"]:
            if isinstance(each.signed, bool):
                if each.signed:
                    header_text = "signal " + each.name + " : signed(0 to " + str(each.size-1) + ");\n"
                else:
                    header_text = "signal " + each.name + " : unsigned(0 to " + str(each.size - 1) + ");\n"
            else:
                header_text = "signal " + each.name + " : std_logic_vector(0 to " + str(each.size - 1) + ");\n"

    return header_text, body_text


def generate_timing(frequency, clock_pin):
    return generate_timing_text(Signal.all_signals, frequency, clock_pin)
