import os
import pygame
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
                'mounted archer':2,
                'wizard':1,
                'arch_mage':1,
                'king':1,
                'cook':0.5,
                'doctor':0.5,
                'transport_boat':1.5,
                'attack_boat':2}

std_attack_range = {'villager':(1,1),
                    'infantry':(1,1),
                    'archer':(2,4),
                    'cavalry':(1,1),
                    'mounted archer':(2,4),
                    'wizard':(1,2),
                    'arch_mage':(1,5),
                    'king':(1,1),
                    'cook':(0,0),
                    'doctor':(0,0),
                    'transport_boat':(0,0),
                    'attack_boat':(1,3)}

std_help_range = {  'villager':(1,1),
                    'infantry':(1,1),
                    'archer':(1,1),
                    'cavalry':(1,1),
                    'mounted archer':(1,1),
                    'wizard':(1,2),
                    'arch_mage':(1,5),
                    'king':(1,1),
                    'cook':(1,1),
                    'doctor':(1,1),
                    'transport_boat':(1,1),
                    'attack_boat':(1,1)}

std_strength = {'villager':0.3,
                'infantry':1,
                'archer':0.6,
                'cavalry':2,
                'mounted archer':1,
                'wizard':1,
                'arch_mage':2,
                'king':2,
                'cook':0.3,
                'doctor':0.3,
                'transport_boat':0,
                'attack_boat':1} #attack boat only attack other boats

std_defense =  {'villager':0.3,
                'infantry':1,
                'archer':0.6,
                'cavalry':2,
                'mounted archer':1,
                'wizard':1,
                'arch_mage':2,
                'king':5,
                'cook':0.3,
                'doctor':0.3,
                'transport_boat':1,
                'attack_boat':1} #attack boat only attack other boats

std_distance = 5

units_type_to_load = ["infantry", "wizard"]

assert set(std_help_range.keys()) == set(std_attack_range.keys()) == set(std_type_cost.keys())

##NEUTRAL = 0
##SUBTLE = 1
##BRUTAL = 2
##DISCIPLINED = 3

#INTELLIGENCE = 1
#AGILITY = 2
#FORCE = 3

SOLAR = 1
LUNAR = 2
STELLAR = 3

BASE_RACE_FACTOR = 0.2
RACE_FIGHT_FACTOR = {   (SOLAR,LUNAR):1.+BASE_RACE_FACTOR,
                        (LUNAR,STELLAR):1.+BASE_RACE_FACTOR,
                        (STELLAR,SOLAR):1.+BASE_RACE_FACTOR}
for a,b in SPECIALIZATIONS_FACTORS:
    SPECIALIZATIONS_FACTORS[(b,a)] = 1. - BASE_RACE_FACTOR

class Race:
    def __init__(self, name, baserace, racetype, me, color="blue"):
        self.name = name
        self.baserace = baserace
        self.racetype = racetype
        self.base_material_cost = std_cost_material.copy()
        self.base_max_dist = std_distance
        self.base_attack_range = std_attack_range.copy()
        self.base_help_range = std_help_range.copy()
        self.base_terrain_attack = {}
        self.base_strength = std_strength.copy()
        self.base_defense = std_defense.copy()
        self.unit_types = {}
        self.me = me
        self.color = color
        for unit_type in units_type_to_load:
            self.add_type(unit_type, "sprites/"+baserace+"_"+unit_type)


    def add_type(self, type_name, imgs_fn, factor=1.):
        imgs = unit.load_sprites(imgs_fn, self.color)
        assert type_name not in self.unit_types
        u = unit.Unit(type_name, self.me, imgs, type_name, factor)
        u.race = self
        #the following properties will be computed during the finalisation:
##        u.max_dist = self.base_max_dist * std_type_cost.get(type_name, 1.)
##        u.attack_range = std_attack_range.get(type_name, 1)
##        u.help_range = std_help_range.get(type_name, 1)
##        u.cost = self.base_material_cost.copy()
##        u.terrain_attack = self.base_terrain_attack.copy()
        self.unit_types[type_name] = u
        if os.path.exists(imgs_fn+"_footprint.png"):
            u.footprint = pygame.image.load(imgs_fn+"_footprint.png")
        else:
            u.footprint = pygame.image.load("sprites/footprint.png")
        return u

    def finalize(self):
        for type_name in self.unit_types:
            u = self[type_name]
            if u.max_dist is None:
                u.max_dist = self.base_max_dist * std_type_cost.get(type_name, 1.)
            if u.attack_range is None:
                u.attack_range = self.base_attack_range.get(type_name, 1)
            if u.help_range is None:
                u.help_range = self.base_help_range.get(type_name, 1)
            if u.strength is None:
                u.strength = self.base_strength.get(type_name)
            if u.defense is None:
                u.defense = self.base_defense.get(type_name)
            #
            u.cost = fusion_dicts(u.cost, self.base_cost)
            u.terrain_attack = fusion_dicts(u.terrain_attack, self.base_terrain_attack)
        self.make_consistant()

    def make_consistant(self): !!
        for type_name in self.unit_types:
            u = self[type_name]
            if u.strength != self.base_strength.get(type_name):
                self.base_strength = u.strength
            if u.defense != self.base_defense.get(type_name):
                self.base_defense = u.defense

    def __getitem__(self, key):
        return self.unit_types[key]


def fusion_dicts(primary, secondary):
    d = {}
    for key in primary:
        d[key] = primary[key]
    for key in secondary:
        if not(key in primary):
            d[key] = secondary[key]
    return d
