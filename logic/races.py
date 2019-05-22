from . import unit

std_cost_material = {'Deep water': float("inf"),
                     'Grass': 1.5,
                     'Rock': 3.5,
                     'Sand': 3.5,
                     'Shallow water': float("inf"),
                     'Snow': 5,
                     'Thin snow': 4,
                     'Water': float("inf"),
                     'outside': float("inf"),
                     'forest': 4,
                     'cobblestone':1,
                     'village':1,
                     'wood':1,
                     'river':6,
                     'bush':5}


std_type_cost = {'villager':1,
                'infantry':1,
                'archer':1,
                'cavalry':2,
                'wizard':1,
                'cook':0.5,
                'doctor':0.5,
                'transport boat':1.5,
                'attack boat':2}

std_distance = 5


class Race:
    def __init__(self, name, me):
        self.name = name
        self.base_cost = std_cost_material.copy()
        self.base_max_dist = std_distance
        self.unit_types = {}
        self.me = me

    def add_type(self, type_name, img_fn, factor=1.):
        assert type_name not in self.unit_types
        u = unit.Unit(type_name, self.me, img_fn, "", factor)
        u.race = self
        u.max_dist = self.base_max_dist * std_type_cost.get(type_name, 1.)
        u.cost = self.base_cost.copy()
        self.unit_types[type_name] = u
        return u

    def __getitem__(self, key):
        return self.unit_types[key]
