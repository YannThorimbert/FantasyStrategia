import random, os
import pygame, thorpy
from PyWorld2D.mapobjects.objects import MapObject
import PyWorld2D.constants as const
from FantasyStrategia.logic.races import RACE_FIGHT_FACTOR



SPRITES_KEYS = ["idle", "right", "left", "down", "up", "lattack", "rattack", "die", "head"]
COLORS_HIGHLIGHTS = {"red":(255,0,0), "yellow":(255,255,0), "blue":(0,0,255)}
HIGHLIGHT_BLUR = 3
HIGHLIGHT_INFLATE = 10

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}

NEUTRAL_COLOR = "white"
COLORS = {"blue":((160,195,210), (110,160,185), (76,95,128)), #SRC_COLOR
          "red":((255,175,140), (230,140,90), (175,75,56)),
          "green":((195,255,160), (160,230,110), (95,175,76)),
          "black":((130,)*3, (90,)*3, (75,)*3),
          "white":((245,)*3, (220,)*3, (200,)*3)}


ANIM_LOOP = 0
ANIM_ONCE = 1


BASE_FIGHT_FACTOR = 1.5
ATTACKING_DAMAGE_FACTOR = 1.2
FIGHT_AMPLITUDE = 1.3 #control the length of the fights
FIGHT_RANDOMNESS = 0.6
FIGHT_R0 = 1. - FIGHT_RANDOMNESS/2.
def get_random_factor_fight():
    """Returns a float in [1-FIGHT_RANDOMNESS/2, 1+FIGHT_RANDOMNESS/2]."""
    r = random.random() * FIGHT_RANDOMNESS
    return FIGHT_AMPLITUDE*(FIGHT_R0 + r)




class Unit(MapObject):
    unit_id = 0

    @staticmethod
    def get_saved_attributes():
        return MapObject.get_saved_attributes() + ["team"]

    def __init__(self, type_name, editor, sprites, name=None, factor=1., relpos=(0,0),
                    build=True, new_type=True):
        self.stop_animation = float("inf")
        self.stop_animation_func = None
        self.set_animation_type("loop")
        self.animation_step = 0
        self.grayed = []
        self.highlights = {}
        self.sprites_ref = {}
        if sprites:
            imgs = []
            isprite = 0
            for key in SPRITES_KEYS:
                sprites_for_this_key, frame_type = sprites[key]
                imgs.extend(sprites_for_this_key)
                n = len(sprites_for_this_key)
                self.sprites_ref[key] = (isprite, n, frame_type)
                isprite += n
        else:
            imgs = [""]
        MapObject.__init__(self, editor, imgs, type_name, factor, relpos, build,
                            new_type)
        self.can_interact = True
        #
        self.max_dist = None
        self.attack_range = None
        self.shot_frequency = None
        self.help_range = None
        self.cost = None
        self.base_number = None
        self.material_cost = {}
        self.terrain_attack = {}
        self.object_defense = {}
        self.strength = None
        self.defense = None
        #
        self.race = None
        self.game = None
        #
        self.walk_img = {}
        self.set_frame_refresh_type(2) #type fast
        self.vel = 0.07
        self.current_isprite = 0
        self.team = None
        self.footprint = None
        self.projectile1 = None #projectile used in close battle
        self.is_grayed = False
        self.id = Unit.unit_id
        Unit.unit_id += 1

    def make_grayed(self):
        self.is_grayed = True
        self.hide = True
        imgs = self.race[self.name].grayed
        obj = MapObject(self.game.me, imgs[self.game.me.zoom_level])
        obj.imgs_z_t = imgs
        obj = self.game.add_object(self.cell.coord, obj, 1)
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.get_map_time = self.get_map_time
        obj.get_current_from = self.get_current_frame
        obj.name = "grayed_"+self.name


    def _spawn_possible_destinations(self, x, y, tot_cost, path_to_here, score):
        for dx,dy in DELTAS:
            cx, cy = x+dx, y+dy #next cell
            next_cell = self.editor.lm.get_cell_at(cx,cy)
            if next_cell:
                if next_cell.unit:
                    continue
                elif next_cell.coord in self.game.burning:
                    continue
                no_key_value = float("inf"), None
                best_score, best_path = score.get((cx,cy), no_key_value)
                #compute the cost of the current path ##########################
                for obj in next_cell.objects:
                    if not isinstance(obj, Unit):
                        if next_cell.coord in self.game.bridges:
                            this_tot_cost = self.material_cost["bridge"]
                            break
                        elif not isinstance(obj, InteractiveObject):
                            this_tot_cost = self.material_cost[obj.str_type]
                            break
                else: #if break is never reached
                    this_tot_cost = self.material_cost[next_cell.material.name]
                this_tot_cost += tot_cost #+ cost so far
                ################################################################
                if this_tot_cost <= self.max_dist: #should update the best
                    if this_tot_cost < best_score:
                        new_best_path = path_to_here + [(cx,cy)]
                        score[(cx,cy)] = this_tot_cost, new_best_path
                        self._spawn_possible_destinations(cx, cy, this_tot_cost,
                                                          new_best_path, score)

    def get_possible_destinations(self):
        score = {}
        x,y = self.cell.coord
        self._spawn_possible_destinations(x, y, 0., [self.cell.coord], score)
        return score

    def get_all_players(self):
        return self.game.get_players_from_team(self.team)

    def can_fight(self):
        return self.attack_range[0] > 0

    def copy(self, obj=None):
        """The copy references the same images as the original !"""
        self.ncopies += 1
        if obj is None:
            obj = self.__class__(self.str_type, self.editor, None, self.name,
                                self.factor, list(self.relpos), new_type=False)
        obj.original_imgs = self.original_imgs
        obj.nframes = self.nframes
        obj.imgs_z_t = self.imgs_z_t
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.relpos = list(self.relpos)
        obj.int_type = self.int_type
        obj.quantity = self.quantity
        obj.fns = self.fns
        #
        obj.race = self.race
        obj.vel = self.vel
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.sprites_ref = self.sprites_ref.copy()
        obj.is_ground = self.is_ground
        obj.always_drawn_last = self.always_drawn_last
        obj.can_interact = self.can_interact
        obj.highlights = self.highlights
        obj.team = self.team
        #
        obj.cost = self.cost
        obj.base_number = self.base_number
        obj.material_cost = self.material_cost.copy()
        obj.max_dist = self.max_dist
        obj.help_range = self.help_range
        obj.attack_range = self.attack_range
        obj.shot_frequency = self.shot_frequency
        obj.terrain_attack = self.terrain_attack
        obj.object_defense = self.object_defense
        obj.strength = self.strength
        obj.defense = self.defense
        #
        obj.footprint = self.footprint
        obj.projectile1 = self.projectile1
        return obj

    def deep_copy(self, obj=None):
        if obj is None:
            obj = self.__class__(self.str_type, self.editor, None, self.name,
                                self.factor, list(self.relpos), new_type=False)
        obj.quantity = self.quantity
        obj.fns = self.fns
        obj.original_imgs = [i.copy() for i in self.original_imgs]
        obj.nframes = len(obj.original_imgs)
        obj.imgs_z_t = []
        for frame in range(len(self.imgs_z_t)):
            obj.imgs_z_t.append([])
            for scale in range(len(self.imgs_z_t[frame])):
                obj.imgs_z_t[frame].append(self.imgs_z_t[frame][scale].copy())
##        for imgs in self.imgs_z_t:
##            obj.imgs_z_t = [i.copy() for i in imgs]
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.relpos = list(self.relpos)
        obj.int_type = self.int_type
        #
        obj.race = self.race
        obj.vel = self.vel
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.sprites_ref = self.sprites_ref.copy()
        obj.can_interact = self.can_interact
        obj.is_ground = self.is_ground
        obj.always_drawn_last = self.always_drawn_last
        obj.team = self.team
        #
        obj.cost = self.cost
        obj.base_number = self.base_number
        obj.material_cost = self.material_cost.copy()
        obj.max_dist = self.max_dist
        obj.help_range = self.help_range
        obj.attack_range = self.attack_range
        obj.shot_frequency = self.shot_frequency
        obj.terrain_attack = self.terrain_attack.copy()
        obj.object_defense = self.object_defense.copy()
        obj.strength = self.strength
        obj.defense = self.defense
        #
        obj.highlights = {}
        for color in self.highlights:
            obj.highlights[color] = [i.copy() for i in self.highlights[color]]
        obj.footprint = self.footprint.copy()
        obj.projectile1 = self.projectile1.copy()
        return obj

    def get_current_highlight(self, color):
        return self.highlights[color][self.editor.zoom_level]

    def _free_get_current_img(self):
        frame = self.get_current_frame() + self.current_isprite
        return self.imgs_z_t[self.editor.zoom_level][frame]

    def _once_get_current_img(self):
        delta = self.get_map_time() - self.animation_step
        if delta >= self.stop_animation:
            print("stop", self.id, self.get_map_time())
            self.stop_animation_func()
        if delta >= self.nframes:
            frame = self.nframes - 1 + self.current_isprite
        else:
            frame = delta + self.current_isprite
        return self.imgs_z_t[self.editor.zoom_level][frame]

    def set_sprite_type(self, key):
        i,n,t = self.sprites_ref[key]
        self.current_isprite = i
        self.nframes = n
        self.set_frame_refresh_type(t)

    def refresh_translation_animation(self):
        if self.animation_type == ANIM_LOOP:
            delta = MapObject.refresh_translation_animation(self)
            key = DELTA_TO_KEY[delta]
            self.set_sprite_type(key)

    def set_animation_type(self, new_animation_type):
        """new_animation_type is either "once" or "loop"."""
        if new_animation_type == "loop":
            self.animation_type = ANIM_LOOP
            self.get_current_img = self._free_get_current_img
            self.animation_step = 0
        elif new_animation_type == "once":
            self.animation_type = ANIM_ONCE
            self.get_current_img = self._once_get_current_img
            self.animation_step = self.get_map_time()

    def remove_from_game(self):
        self.game.units.remove(self)
        self.game.me.dynamic_objects.remove(self)
        self.remove_from_cell()

    def die_after(self, duration):
        self.set_sprite_type("die")
        self.set_animation_type("once")
        slowness = self.game.me.lm.get_slowness(self._refresh_frame_type)
        self.stop_animation = self.game.me.fps / slowness
        self.stop_animation_func = self.remove_from_game

    def reset_stop_animation(self):
        self.stop_animation = float("inf")
        self.stop_animation_func = None


    def build_imgs(self):
        MapObject.build_imgs(self)
        self.build_highlighted_idles()
        self.build_grayed_idles()

    def build_highlighted_idles(self):
        frame = self.sprites_ref["idle"][0]
        self.highlights = {}
        for color in COLORS_HIGHLIGHTS:
            self.highlights[color] = []
            rgb = COLORS_HIGHLIGHTS[color]
            for z in range(len(self.editor.zoom_cell_sizes)):
                img = self.imgs_z_t[z]
                img = img[frame]
                shad = thorpy.graphics.get_shadow(img,
                                    shadow_radius=HIGHLIGHT_BLUR, black=255,
                                    color_format="RGBA", alpha_factor=1.,
                                    decay_mode="exponential", color=rgb,
                                    sun_angle=45., vertical=True,
                                    angle_mode="flip",
                                    mode_value=(False, False))
                size = shad.get_rect().inflate(HIGHLIGHT_INFLATE,HIGHLIGHT_INFLATE).size
                shad = pygame.transform.smoothscale(shad, size)
                self.highlights[color].append(shad)


    def build_grayed_idles(self):
##        frame = self.sprites_ref["idle"][0]
        isprite, n, frame_type = self.sprites_ref["idle"]
        for z in range(len(self.editor.zoom_cell_sizes)):
            self.grayed.append([])
            imgs = self.imgs_z_t[z]
            for i in range(isprite, isprite+n):
                shad = imgs[i].copy()
                w,h = shad.get_size()
                TRANSP = (255,)*4
                K = 0.75
                for x in range(w):
                    for y in range(h):
                        rgba = shad.get_at((x,y))
                        if rgba != TRANSP:
                            r,g,b,a = rgba
                            r = max(0, int(K*r))
                            g = max(0, int(K*r))
                            b = max(0, int(K*r))
                            shad.set_at((x,y), (r,g,b,a))
                self.grayed[-1].append(shad)

    def get_coords_within_range(self, rng):
        dmin,dmax = rng
        if dmax == 0: #quicker
            return []
        elif dmax == 1: #quicker
            return DELTAS
        else:
            cells = []
            for dx in range(-dmax,dmax+1):
                for dy in range(-dmax,dmax+1):
                    if dmin <= abs(dx) + abs(dy) <= dmax:
                        cells.append((dx, dy))
            return cells

    def get_coords_in_attack_range(self):
        return self.get_coords_within_range(self.attack_range)

    def get_coords_in_help_range(self):
        return self.get_coords_within_range(self.help_range)

    def get_terrain_name_for_fight(self): #ajouter forest et compagnie
        if self.cell.coord in self.game.bridges: #bypass water
            return "bridge"
        for obj in self.cell.objects:
            if obj.str_type == "river":
                return "river"
            elif obj.str_type == "cobblestone":
                return "cobblestone"
        return self.cell.material.name.lower()

    def get_terrain_bonus(self):
        d = max([self.object_defense.get(o.str_type,1.) for o in self.cell.objects])
        terrain = self.get_terrain_name_for_fight()
        return self.terrain_attack.get(terrain, 1.)*d

    def get_fight_result(self, other, terrain_bonus1, terrain_bonus2, self_is_defending): #-1, 0, 1
        """-1: self looses, 0: draw, 1: self wins"""
        self_race = self.race.racetype
        other_race = other.race.racetype
        f = RACE_FIGHT_FACTOR.get((self_race, other_race), 1.)
        r = get_random_factor_fight()
        damage_to_other = terrain_bonus1 * r * f * self.strength / other.defense
        if damage_to_other > 1.:
            return 1
        else:
            f = RACE_FIGHT_FACTOR.get((other_race, self_race), 1.)
            damage_from_other = terrain_bonus2 * r * f * other.strength / self.defense
            if self_is_defending:
                damage_from_other *= ATTACKING_DAMAGE_FACTOR
            if damage_from_other > 1.:
                return -1
        return 0

    def get_distant_attack_result(self, other, terrain_bonus1, terrain_bonus2, self_is_defending): #-1, 0, 1
        """-1: self looses, 0: draw, 1: self wins"""
        self_race = self.race.racetype
        other_race = other.race.racetype
        f = RACE_FIGHT_FACTOR.get((self_race, other_race), 1.)
        r = get_random_factor_fight()
        damage_to_other = terrain_bonus1 * r * f * self.strength / other.defense
        if self_is_defending:
            damage_to_other *= 0.5
        return damage_to_other

    def get_all_surrounding_units(self):
        units = []
        x,y = self.cell.coord
        for dx,dy in DELTAS:
            unit = self.game.get_unit_at(x+dx,y+dy)
            if unit:
                units.append(unit)
        return units

    def get_all_surrounding_ennemies(self):
        return [u for u in self.get_all_surrounding_units() if u.team != self.team]


def get_unit_sprites(fn,  colors="blue", deltas=None, s=32, ckey=(255,255,255)):
    imgs = []
    sprites = pygame.image.load(fn)
    if colors != "blue":
        if isinstance(colors,str):
            colors = COLORS[colors]
        for i in range(3):
            src = COLORS["blue"][i]
            dst = colors[i]
            thorpy.change_color_on_img_ip(sprites, src, dst)
    n = sprites.get_width() // s
    if not deltas:
        deltas = [(0,0) for i in range(n)]
    x = 0
    for i in range(n):
        surf = pygame.Surface((s,s))
        surf.fill(ckey)
        surf.set_colorkey(ckey)
        dx, dy = deltas[i]
        surf.blit(sprites, (dx,dy), pygame.Rect(x,0,s,s))
        imgs.append(surf)
        x += s
    return imgs

def load_unit_sprites(fn, colors="blue", h=const.FAST, v=const.FAST, i=const.SLOW):
##    deltas_lr =  [(0,0), (0,-1), (0,-2), (0,-1), (0,0), (0,0)]
    left = get_unit_sprites(fn+"_left.png",colors)#, deltas_lr)
    right = get_unit_sprites(fn+"_right.png",colors)
    down = get_unit_sprites(fn+"_down.png",colors)
    up = get_unit_sprites(fn+"_up.png",colors)
    idle = get_unit_sprites(fn+"_idle.png",colors)
    lattack = get_unit_sprites(fn+"_left_attack.png",colors)
    rattack = get_unit_sprites(fn+"_right_attack.png",colors)
    die = get_unit_sprites(fn+"_die.png",colors)
    head = get_unit_sprites(fn+"_head.png",colors)
    sprites = {"right":(right,h), "left":(left,h), "down":(down,v), "up":(up,v),
                "idle":(idle,i),
                "lattack":(lattack,i), "rattack":(rattack,i),
                "die":(die,h), "head":(head,h)}
    return sprites



class InteractiveObject(Unit):

    @staticmethod
    def get_saved_attributes():
        return Unit.get_saved_attributes() + ["color"]

    def __init__(self, name, editor, sprites, race=None,
                 sprites_keys=("idle",), factor=1., relpos=(0,0), build=True,
                 new_type=True, str_type=None):
        self.stop_animation = float("inf")
        self.stop_animation_func = None
        self.set_animation_type("loop")
        self.animation_step = 0
        self.grayed = []
        self.highlights = {}
        self.sprites_ref = {}
        self.race = race
        if race is None:
            self.color = NEUTRAL_COLOR
        else:
            self.color = self.race.color
        if isinstance(sprites,str):
            fn = str(sprites)
            sprites = {}
            for key in sprites_keys:
                sprites[key] = get_unit_sprites(fn+"_"+key+".png", self.color), const.NORMAL
        elif isinstance(sprites,tuple):
            img,key = sprites
            sprites = {}
            sprites[key] = [img], const.NORMAL
        if sprites:
            imgs = []
            isprite = 0
            for key in sprites_keys:
                sprites_for_this_key, frame_type = sprites[key]
                imgs.extend(sprites_for_this_key)
                n = len(sprites_for_this_key)
                self.sprites_ref[key] = (isprite, n, frame_type)
                isprite += n
        else:
            imgs = [""]
        MapObject.__init__(self, editor, imgs, name, factor, relpos, build,
                            new_type, str_type)
        #
        self.cost = None
        self.base_number = None
        self.max_dist = None
        self.attack_range = None
        self.shot_frequency = None
        self.help_range = None
        self.material_cost = {}
        self.terrain_attack = {}
        self.object_defense = {}
        self.strength = None
        self.defense = None
        #
        self.race = None
        self.game = None
        #
        self.walk_img = {}
        self.set_frame_refresh_type(2) #type fast
        self.vel = 0.07
        self.current_isprite = 0
        self.team = None
        self.footprint = None
        self.projectile1 = None #projectile used in close battle
        self.id = Unit.unit_id
        Unit.unit_id += 1
        self.can_interact = True

    def copy(self):
        obj = InteractiveObject(self.name, self.editor, None, self.race,
                                self.factor, list(self.relpos), new_type=False,
                                str_type=self.str_type)
        obj = Unit.copy(self, obj)
        obj.color = self.color
        return obj

    def deep_copy(self):
        obj = InteractiveObject(self.name, self.editor, None, self.race,
                                self.factor, list(self.relpos), new_type=False,
                                str_type=self.str_type)
        obj = Unit.deep_copy(self, obj)
        obj.color = self.color
        return obj

    def remove_from_game(self):
##        self.game.objects.remove(self)
        self.game.me.dynamic_objects.remove(self)
        self.remove_from_cell()
