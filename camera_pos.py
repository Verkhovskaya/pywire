from signal_v2 import Signal
from builder_v2 import generate_vhdl


newLine = 	Signal(1, 	io="in", 	name="newLine")
newFrame = 	Signal(1, 	io="in", 	name="newFrame")
newPixel = 	Signal(1, 	io="in", 	name="newPixel")
xPos = 		Signal(10, 	io="out", 	name="xPos")
yPos = 		Signal(10, 	io="out", 	name="yPos")
valid = 	Signal(1, 	io="out", 	name="valid")

def track(current, clear, increment):
	if bool(clear):
		return "0"
	elif bool(increment):
		return "+", current, 1
	else:
		return current


xPos.drive(track, args=(xPos, newPixel, newLine))
yPos.drive(track, args=(yPos, newLine, newFrame))
print generate_vhdl(xPos, yPos)

def is_valid(newLine, newFrame, newPixel):
	if newLine
valid.drive()

class Entity:
	def __init__(self, signals, links):
		print signals
		print links

class Camera_pos(Entity):
	def __init__(self, links):
		Entity.__init__(self, signals=(xPos, newPixel, yPos, newLine, newFrame), links=links)
