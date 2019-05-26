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


# faire un objet quand meme, juste pour storer : cost factor, attack range et degats associes, defense, besoins en nourriture, + vulnerabilite a certains types ?
# Ou alors faire un systeme avec un dict qui store les exceptions a la regle
# class UnitType:
#     def ???

std_type_cost = {'villager':1,
                'infantry':1,
                'archer':1,
                'cavalry':2,
                'mounted archer':2,
                'wizard':1,
                'arch mage':1,
                'king':1,
                'cook':0.5,
                'doctor':0.5,
                'transport boat':1.5,
                'attack boat':2}

std_attack_range = {'villager':(1,1),
                    'infantry':(1,1),
                    'archer':(2,4),
                    'cavalry':(1,1),
                    'mounted archer':(2,4),
                    'wizard':(1,2),
                    'arch mage':(1,5),
                    'king':(1,1),
                    'cook':(0,0),
                    'doctor':(0,0),
                    'transport boat':(0,0),
                    'attack boat':(1,3)}

std_help_range = {'villager':(1,1),
                    'infantry':(1,1),
                    'archer':(1,1),
                    'cavalry':(1,1),
                    'mounted archer':(1,1),
                    'wizard':(1,2),
                    'arch mage':(1,5),
                    'king':(1,1),
                    'cook':(1,1),
                    'doctor':(1,1),
                    'transport boat':(1,1),
                    'attack boat':(1,1)}

std_distance = 5




class Race:
    def __init__(self, name, me):
        self.name = name
        self.base_cost = std_cost_material.copy()
        self.base_max_dist = std_distance
        self.unit_types = {}
        self.me = me

    def add_type(self, type_name, imgs_fn, factor=1.):
        assert type_name not in self.unit_types
        u = unit.Unit(type_name, self.me, imgs_fn, type_name, factor)
        u.race = self
        u.max_dist = self.base_max_dist * std_type_cost.get(type_name, 1.)
        u.attack_range = std_attack_range.get(type_name, 1)
        u.help_range = std_help_range.get(type_name, 1)
        u.cost = self.base_cost.copy()
        self.unit_types[type_name] = u
        return u

    def __getitem__(self, key):
        return self.unit_types[key]
