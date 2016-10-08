# Point class, define operations to be treated as number
from numbers import Number
from collections import namedtuple
from math import sqrt

class Point(namedtuple('PointBase', ['x', 'y'])):
    __slots__ = ()  # Saves memory, avoiding the need to create __dict__ for each interval

    # def __new__(cls, x, y):
    #     return super(Point, cls).__new__(cls, x, y)

    def zero():
        return Point(0,0)

    def euclidean_dist(self, other):
        if isinstance(other,type(self)):
            return (self - other).dist_to_org()
        else:
            return NotImplemented

    def dist_to_org(self):
        return sqrt(self.x**2 + self.y**2)

    def __add__(self, other):
        if isinstance(other,type(self)):
            return Point(self.x + other.x, self.y + other.y)
        if isinstance(other, Number):
            return Point(self.x + other, self.y + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other,type(self)):
            return Point(self.x - other.x, self.y - other.y)
        if isinstance(other, Number):
            return Point(self.x - other, self.y - other)
        else:
            return NotImplemented

    def __neg__(self):
        return Point(- self.x, -self.y)

    def __mul__(self, other):
        return NotImplemented

    def __floordiv__(self, other):
        if isinstance(other, Number):
            return Point(self.x / other, self.y / other)
        else:
            return NotImplemented

    def __mod__(self, other):
        if isinstance(other, Number):
            return Point(self.x % other, self.y % other)
        else:
            return NotImplemented

    def __divmod__(self, other):
        if isinstance(other, Number):
            return Point(self.x % other, self.y % other)
        else:
            return NotImplemented
    def __eq__(self, other): 
        if isinstance(other,type(self)):
            return (self.x == other.x and self.y == other.y)
        else:
            return NotImplemented

    def __cmp__(self, other):
        def cmp(a, b):
            return (a > b) - (a < b)
        if isinstance(other,type(self)):
            val = cmp(self.x, other.x)
            if val == 0:
                return cmp(self.y, other.y)
            return val
        else:
            return NotImplemented

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __repr__(self):
        if isinstance(self.x, Number):
            s_x = str(self.x)
            s_y = str(self.y)
        else:
            s_x = repr(self.x)
            s_y = repr(self.y)
        return "Point({0}, {1})".format(s_x, s_y)
        
    __str__ = __repr__

    def __hash__(self):
        """
        Depends on begin and end only.
        :return: hash
        :rtype: Number
        """
        return hash((self.x, self.y))

    def copy(self):
        """
        Shallow copy.
        :return: copy of self
        :rtype: Interval
        """
        return Point(self.x, self.y)
    
    def __reduce__(self):
        """
        For pickle-ing.
        :return: pickle data
        :rtype: tuple
        """
        return Interval, self.x, self.y