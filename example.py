from library import Data, Entity
from library import b, i

e = Entity(50)
number_of_planets = 3


# POI stands for planet of interest
def x_force_calc((poi_x, poi_y, other_x, other_y)):
	poi_x, poi_y, other_x, other_y = [b(x) for x in (poi_x, poi_y, other_x, other_y)]
	if poi_x == other_x and poi_y == other_y:
		return 0
	else:
		return b((other_x-poi_x)/((other_x-poi_x)**2+(other_y-poi_y)**2))


def y_force_calc((poi_x, poi_y, other_x, other_y)):
	poi_x, poi_y, other_x, other_y = [b(x) for x in (poi_x, poi_y, other_x, other_y)]
	if poi_x == other_x and poi_y == other_y:
		return 0
	else:
		return b((other_y-poi_y)/((other_x-poi_x)**2+(other_y-poi_y)**2))


def add(*args):
	temp = 0
	for each in args:
		temp += i(each)
	return b(temp)


x_posit = [Data(4) for x in range(number_of_planets)]
y_posit = [Data(4) for x in range(number_of_planets)]
x_force = [Data(4) for x in range(number_of_planets)]
y_force = [Data(4) for x in range(number_of_planets)]
x_speed = [Data(4) for x in range(number_of_planets)]
y_speed = [Data(4) for x in range(number_of_planets)]
inter_forces_x = [[Data(4) for x in range(number_of_planets)] for y in range(number_of_planets)]
inter_forces_y = [[Data(4) for x in range(number_of_planets)] for y in range(number_of_planets)]


for actor in range(number_of_planets):
	for receiver in range(number_of_planets):
		e.build((x_posit[receiver], y_posit[receiver], x_posit[actor], y_posit[actor]), x_force_calc, inter_forces_x[receiver][actor])
		e.build((x_posit[receiver], y_posit[receiver], x_posit[actor], y_posit[actor]), y_force_calc, inter_forces_y[receiver][actor])


for i in range(number_of_planets):
	e.build(inter_forces_x[i], add, x_force[i])
	e.build(inter_forces_y[i], add, y_force[i])
	e.build((x_force[i], x_speed[i]), add, x_speed[i][0])
	e.build((y_force[i], y_speed[i]), add, y_speed[i][0])
	e.build((x_posit[i], x_speed[i]), add, x_posit[i][0])
	e.build((y_posit[i], y_speed[i]), add, y_posit[i])

e.port(x_force[0], "out")

print e.generate_vhdl()