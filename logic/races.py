import os
import pygame
from . import unit
import PyWorld2D.constants as const

std_material_cost = {'Deep water': float("inf"),
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

std_max_dist = {'villager':0.8,
                'infantry':1,
                'archer':1,
                'cavalry':2,
                'mounted archer':2,
                'wizard':1,
                'arch_wizard':1,
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
                    'arch_wizard':(1,5),
                    'king':(1,1),
                    'cook':(0,0),
                    'doctor':(0,0),
                    'transport_boat':(0,0),
                    'attack_boat':(1,3)}


std_shot_frequency = {'villager':1,
                    'infantry':1,
                    'archer':100,
                    'cavalry':1,
                    'mounted archer':100,
                    'wizard':50,
                    'arch_wizard':30,
                    'king':1,
                    'cook':1,
                    'doctor':1,
                    'transport_boat':1,
                    'attack_boat':30}

std_help_range = {  'villager':(1,1),
                    'infantry':(1,1),
                    'archer':(1,1),
                    'cavalry':(1,1),
                    'mounted archer':(1,1),
                    'wizard':(1,2),
                    'arch_wizard':(1,5),
                    'king':(1,1),
                    'cook':(1,1),
                    'doctor':(1,1),
                    'transport_boat':(1,1),
                    'attack_boat':(1,1)}

std_strength = {'villager':0.6,
                'infantry':1,
                'archer':0.6,
                'cavalry':2,
                'mounted archer':1,
                'wizard':1,
                'arch_wizard':2,
                'king':2,
                'cook':0.3,
                'doctor':0.3,
                'transport_boat':0,
                'attack_boat':1} #attack boat only attack other boats

std_defense =  {'villager':0.6,
                'infantry':1,
                'archer':0.6,
                'cavalry':2,
                'mounted archer':1,
                'wizard':1,
                'arch_wizard':2,
                'king':5,
                'cook':0.3,
                'doctor':0.3,
                'transport_boat':1,
                'attack_boat':1} #attack boat only attack other boats

std_object_defense = {"bush":1.3,
                      "forest":1.5,
                      "village":1.8}

std_distance_factor = 5

units_type_to_load = ["infantry", "wizard", "villager"]

assert set(std_help_range.keys()) == set(std_attack_range.keys()) == set(std_max_dist.keys())

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
##for a,b in RACE_FIGHT_FACTOR:
##    RACE_FIGHT_FACTOR[(b,a)] = 1. - BASE_RACE_FACTOR

class Race:
    def __init__(self, name, baserace, racetype, me, color="blue", team=None):
        self.name = name
        self.baserace = baserace
        self.racetype = racetype
        self.team = team
        #
        self.base_material_cost = std_material_cost.copy()
        self.dist_factor = std_distance_factor
        self.base_terrain_attack = {}
        self.base_object_defense = std_object_defense.copy()
        self.strength_factor = 1.
        self.defense_factor = 1.
        #
        self.unit_types = {}
        self.me = me
        self.color = color
        for unit_type in units_type_to_load:
            self.add_type(unit_type, "sprites/"+baserace+"_"+unit_type)
        self.flag = unit.InteractiveObject("flag", self.me, "sprites/flag",
                                            race=self,
                                            name=self.name+" flag")
##        self.flag.always_drawn_last = True



    def add_type(self, type_name, imgs_fn, factor=1.):
        imgs = unit.load_sprites(imgs_fn, self.color)
        assert type_name not in self.unit_types
        u = unit.Unit(type_name, self.me, imgs, type_name, factor)
        u.race = self
        self.unit_types[type_name] = u
        if os.path.exists(imgs_fn+"_footprint.png"):
            u.footprint = pygame.image.load(imgs_fn+"_footprint.png")
        else:
            u.footprint = pygame.image.load("sprites/footprint.png")
        if os.path.exists(imgs_fn+"_projectile1.png"):
            u.projectile1 = pygame.image.load(imgs_fn+"_projectile1.png")
        else:
            u.projectile1 = pygame.image.load("sprites/projectile1.png")
##            u.projectile1.convert()
##            u.projectile1.set_colorkey((255,255,255))
        return u


    def finalize(self):
        for type_name in self.unit_types:
            u = self[type_name]
            if u.max_dist is None:
                u.max_dist = self.dist_factor * std_max_dist[type_name]
            if u.attack_range is None:
                u.attack_range = std_attack_range[type_name]
            if u.shot_frequency is None:
                u.shot_frequency = std_shot_frequency[type_name]
            if u.help_range is None:
                print("adding help range", type_name, std_help_range[type_name])
                u.help_range = std_help_range[type_name]
            if u.strength is None:
                u.strength = self.strength_factor * std_strength[type_name]
            if u.defense is None:
                u.defense = self.defense_factor * std_defense[type_name]
            #
            u.material_cost = fusion_dicts(u.material_cost,
                                            self.base_material_cost)
            u.terrain_attack = fusion_dicts(u.terrain_attack,
                                            self.base_terrain_attack)
            u.object_defense = fusion_dicts(u.object_defense,
                                            self.base_object_defense)

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
