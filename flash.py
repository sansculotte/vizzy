# -*- coding: utf-8 -*-
from __future__ import print_function, division
import math
import random


class Point(object):

    def __init__(self, x=0.0, y=0.0):
        self._point = (x, y)

    def __repr__(self):
        return '<{0}, {1}>'.format(self.x, self.y)

    @property
    def x(self):
        return self._point[0]

    @x.setter
    def x(self, value):
        self._point[0] = value

    @property
    def y(self):
        return self._point[1]

    @y.setter
    def y(self, value):
        self._point[1] = value

    def translate(self, x, y):
        return Point(
            self.x + x,
            self.y + y
        )


class Vector(object):

    def __init__(self, a: Point, b: Point):
        if not isinstance(a, Point):
            raise TypeError('a must be Point')
        elif not isinstance(b, Point):
            raise TypeError('b must be Point')
        else:
            self._vector = (a, b)

    def __repr__(self):
        return '<Vector {0!r}, {1!r}>'.format(self.a, self.b)

    @staticmethod
    def from_polar(start, phi, length):
        end = Point(
            start.x + length * math.cos(phi),
            start.y + length * math.sin(phi),
        )
        return Vector(start, end)

    @property
    def a(self):
        return self._vector[0]

    @property
    def b(self):
        return self._vector[1]

    @a.setter
    def a(self, value: Point):
        self._vector[0] = value

    @b.setter
    def b(self, value: Point):
        self._vector[1] = value

    @property
    def ab(self):
        return self.b.x - self.a.x, self.b.y - self.a.y

    @property
    def length(self):
        ab = self.ab
        return math.sqrt(ab[0] ** 2 + ab[1] ** 2)

    @property
    def heading(self):
        ab = self.ab
        length = self.length
        return ab[0] / length, ab[1] / length

    @property
    def phi(self):
        x, y = self.heading
        return math.atan2(x, y)


class Flash(object):

    _nodes = []
    _pointer = -1

    def __init__(self, width=500, height=500, start=None, end=None):
        self.width = width
        self.height = height
        self.start = start or Point(0, 0)
        self.end = end or Point(width // 2, height)
        self.add_point(self.start)
        self._pointer = 0

    def __str__(self):
        return ' → '.join(map(str, self._nodes))

    def current_node(self):
        return self._nodes[self._pointer]

    def random_point(self):
        return Point(
            random.randint(0, self.width),
            random.randint(0, self.height)
        )

    def random_walk(self):
        def next_node():
            try:
                a, b = self._nodes[-2:]
            except ValueError:
                return self.random_point()

            last_angle = Vector(a, b).phi
            factor = random.randint(-1, 1)
            rand = random.random()
            if factor == 0:
                new_angle = last_angle + (rand - 0.5) * math.pi / 2
            else:
                new_angle = last_angle - factor * (rand - 0.5) * math.pi / 2

            length = 3
            nv = Vector.from_polar(self.current_node(), new_angle, length)
            return b.translate(*nv.ab)

        self.add_point(next_node())

    def add_point(self, point=None):
        if point is None:
            point = self.random_point()
        self._nodes.append(point)
        self._pointer += 1


if __name__ == '__main__':

    nodes = 23
    flash = Flash(Point(0, 0))
    for n in range(nodes):
        flash.add_point()
