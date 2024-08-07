import typing as t
import click
import math
import random
from numpy import dot
from drawSvg import Drawing, Path


def angle_between(v1, v2):
    u = v1.normal_form
    v = v2.normal_form
    try:
        return math.acos(dot(u, v) / dot(v1.length, v2.length))
    except ValueError:
        print("value error: {0!r} {1!r}".format(u, v))
        return math.pi


class Point:
    def __init__(self, x=0.0, y=0.0):
        self._point = (x, y)

    def __repr__(self):
        return "<{0}, {1}>".format(self.x, self.y)

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
        return Point(self.x + x, self.y + y)

    def within_limits(self, x, y):
        return self.x >= 0 and self.x <= x and self.y >= 0 and self.y <= y

    def within_perimeter(self, other, r):
        return Vector(self, other).length < r


class Vector:
    _vector: t.Tuple[Point, Point]

    def __init__(self, a: Point, b: Point):
        if not isinstance(a, Point):
            raise TypeError("a must be Point")
        elif not isinstance(b, Point):
            raise TypeError("b must be Point")
        else:
            self._vector = (a, b)

    def __repr__(self) -> str:
        return f"<Vector {self.a}, {self.b}>"

    @staticmethod
    def from_polar(start, phi, length) -> "Vector":
        end = Point(
            start.x + length * math.cos(phi),
            start.y + length * math.sin(phi),
        )
        return Vector(start, end)

    @property
    def normal_form(self) -> t.Tuple:
        """
        B - A, assume 0, 0 origin
        """
        return (self.a.x - self.b.x, self.a.y - self.b.y)

    @property
    def a(self) -> Point:
        return self._vector[0]

    @a.setter
    def a(self, value: Point):
        self._vector = (value, self._vector[1])

    @property
    def b(self) -> Point:
        return self._vector[1]

    @b.setter
    def b(self, value: Point):
        self._vector = (self._vector[0], value)

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

    def dot(self, v):
        return self.ab[0] * v.ab[0] + self.ab[1] * v.ab[1]


class Flash:
    __alternate = 0

    def __init__(self, width=500, height=500, start=None, end=None):
        self.width = width
        self.height = height
        self.start = start or Point(width // 2, height)
        self.end = end or Point(width // 2, 0)
        self._nodes: t.List[Point] = []
        self._nodes.append(self.start)

    def __str__(self):
        return " → ".join(map(str, self._nodes))

    def __repr__(self):
        return "<Flash {}>".format(id(self))

    def __len__(self):
        return len(self._nodes)

    @property
    def current_node(self):
        return self._nodes[-1:][0]

    @property
    def random_node(self):
        return self._nodes[random.randint(0, len(self._nodes) - 1)]

    def current_point(self):
        return self.points[-1:][0]

    def random_point(self, x=10, y=10):
        current = self.current_point()
        return Point(
            current.x + random.randint(1, x) - x // 2,
            current.y + random.randint(1, y) - y // 2,
        )

    def alternate(self, a, b):
        self.__alternate = 1 if self.__alternate == 0 else 0
        return a if self.__alternate == 0 else b

    def random_walk(self, length=None, data=0.0, mix=0.0, alternate=False):
        """
        Create a segment in a zig-zag path towards the end point
        :param number:
            length of the segment
        :param float:
            range -1..1 fixed influence on the deflector
        :param float:
            range 0..1 how to mix fixed with random value
        """

        def next_node(length):
            try:
                a, b = self.points[-2:]
            except ValueError:
                return self.random_point(10, 10)

            deflect = random.random() * (1.0 - mix) + data * mix

            factor = (
                self.alternate(0, random.randint(-1, 1))
                if alternate
                else random.randint(-1, 1)
            )

            if factor == 0:
                # why is it off?
                new_angle = math.pi / 2 - Vector(b, self.end).phi + (deflect - 0.5)
                length = length**2
            else:
                new_angle = math.pi / 2 - factor * deflect * math.pi / 2

            nv = Vector.from_polar(b, new_angle, length)
            return b.translate(*nv.ab)

        length = length or random.randint(1, 10)
        node = next_node(length)
        retry = 10
        while not node.within_limits(self.width, self.height):
            node = next_node(length)
            retry -= 1
            # safety catch against infinite looping
            if retry == 0:
                node = self.random_point()
                break
        self.add_node(node)

    def add_node(self, node=None):
        if node is None:
            node = self.random_point()
        self._nodes.append(node)

    @property
    def flashes(self):
        return [n for n in self._nodes if isinstance(n, Flash)]

    @property
    def points(self):
        return [n for n in self._nodes if isinstance(n, Point)]

    @property
    def edges(self):
        return [Vector(self.points[i], p) for i, p in enumerate(self.points[1:])]

    @property
    def path(self):
        path = Path(
            stroke_width=1,
            stroke="black",
            fill="black",
            fill_opacity=0.0,
            stroke_miterlimit=25,  # keep it pointy
        )
        path.M(self.start.x, self.start.y)
        for node in self.points[1:]:
            path.L(node.x, node.y)

        return path

    def render_path(self, thickness=1.0):
        """
        Render double lined, filled flash path
        """
        path = Path(
            stroke_width=1,
            stroke="black",
            fill="black",
            fill_opacity=1.0,
            stroke_miterlimit=99,  # keep it pointy
        )
        path.M(self.start.x, self.start.y)

        for node in self.points[1:]:
            path.L(node.x, node.y)

        backflash = []
        for i, v1 in enumerate(self.edges):
            lp = len(self.points)
            if i < lp - 2:
                v2 = self.edges[i + 1]
                assert v1.b == v2.a
                phi = angle_between(v1, v2)
                distance = thickness - (thickness / (i + 1))
                point = Vector.from_polar(v1.b, phi, distance)
                backflash.append(point)

        for p in reversed(backflash):
            path.L(p.b.x, p.b.y)

        path.Z()
        return path

    def render(self, drawing=None, thickness=1.0):
        drawing = drawing or Drawing(self.width, self.height, origin=(0, 0))
        drawing.append(self.render_path(thickness))
        return drawing


def random_point(max_x: int, max_y: int) -> Point:
    return Point(int(random.random() * max_x), int(random.random() * max_y))


def make_flash(width, height, nodes, verbose):
    flash = Flash(width=width, height=height)
    first_flash = flash
    flashes = [flash]
    for _ in range(nodes):
        if flash.current_point().within_perimeter(flash.end, height / 20):
            flash = Flash(
                width=width,
                height=height,
                start=first_flash.random_node,
                end=random_point(width, height / 2),
            )
            if verbose:
                click.echo(f"new flash started {flash}")

            flashes.append(flash)
        flash.random_walk()
    return flashes


@click.command()
@click.option("-n", "--nodes", help="number of nodes", type=int, default=23)
@click.option("-w", "--width", type=int, default=500)
@click.option("-h", "--height", type=int, default=500)
@click.option("-o", "--outfile", default="/tmp/flash.svg")
@click.option("-v", "--verbose", is_flag=True)
def main(nodes, width, height, outfile, verbose):
    drawing = Drawing(width, height, origin=(0, 0))
    flashes = make_flash(width=width, height=height, nodes=nodes, verbose=verbose)
    for flash in flashes:
        drawing.append(flash.render_path())

    drawing.saveSvg(outfile)
    click.echo(f"saved to {outfile}")


if __name__ == "__main__":
    main()
