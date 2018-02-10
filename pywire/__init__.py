import sys

if sys.version_info[0] != 2:
	raise Exception("Pywire only works with Python 2.7")

from .main import Signal, generate_vhdl, generate_ucf
from .bram import BRAM
from .component import Component, FromText
from .build import build