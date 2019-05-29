import random

class Game:

    def __init__(self, me):
        self.me = me
        self.units = []
        self.objects = []


    def add_unit(self, coord, unit, quantity, team):
        u = self.me.add_unit(coord, unit, quantity)
        u.team = team
        u.game = self
        self.units.append(u)

    def add_object(self, coord, obj, quantity):
        o = self.me.add_unit(coord, obj, quantity)
        self.objects.append(o)

    def get_cell_at(self, x, y):
        return self.me.lm.get_cell_at(x,y)

    def get_unit_at(self, x, y):
        return self.me.lm.get_cell_at(x,y).unit

