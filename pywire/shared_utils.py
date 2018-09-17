import ast


def to_list(args):
	if type(args) is list:
		return args
	elif type(args) is tuple:
		return list(args)
	else:
		return [args]


def match_widths(some_string, some_object):
	ret = []
	for each in some_object:
		ret.append(some_string[:len(each)])
		some_string = some_string[len(each):]
	return ret