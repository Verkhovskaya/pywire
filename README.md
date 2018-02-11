PyWire is an easy-to-use Python library for generating VHDL, designed for use with FPGAs. 

Features:
- Simple and complex functions
- BRAM
- Import components
- Generate timing files

Does not support:
- More than one clock

To install:
```python
pip install pywire
```

Example:
```python
from pywire import *

x = Signal(1, io=“out”, port=“P7”)
y = Signal(1, io=“in”, port=“P42”)

def inverter(x):
	return 1-x

x.drive(inverter, y)
print(vhdl(globals()))
```

The full documentation can be found at http://pywire.readthedocs.io/en/latest/