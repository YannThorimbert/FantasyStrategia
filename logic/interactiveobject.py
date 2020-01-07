import random, os
import pygame, thorpy
from PyWorld2D.mapobjects.objects import MapObject
import PyWorld2D.constants as const
from .unit import get_unit_sprites, NEUTRAL_COLOR

class InteractiveObject(MapObject):
    @staticmethod
    def get_saved_attributes():
        return MapObject.get_saved_attributes() + ["color"]

    def __init__(self, type_name, editor, sprites_fn, race=None, name=None,
                    factor=1., relpos=(0,0), build=True, new_type=True):
        self.type_name = type_name
        self.stop_animation = float("inf")
        self.stop_animation_func = None
        self.set_animation_type("loop")
        self.animation_step = 0
        self.race = race
        if self.race is None:
            self.color = NEUTRAL_COLOR
        else:
            self.color = self.race.color
        if isinstance(sprites_fn, str):
            self.sprites = get_unit_sprites(sprites_fn, self.color)
        else:
            self.sprites = sprites_fn
        self.anim_speed = const.NORMAL
        self.highlights = {}
        MapObject.__init__(self, editor, self.sprites, type_name, factor, relpos, build,
                            new_type)


    def copy(self):
        """The copy references the same images as the original !"""
        self.ncopies += 1
        obj = self.__class__(self.type_name, self.editor, None, self.name, self.factor,
                        list(self.relpos), new_type=False)
        obj.original_imgs = self.original_imgs
        obj.nframes = self.nframes
        obj.imgs_z_t = self.imgs_z_t
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.object_type = self.object_type
        obj.quantity = self.quantity
        obj.fns = self.fns
        obj.race = self.race
        obj.color = self.color
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.sprites = self.sprites.copy()
        obj.is_ground = self.is_ground
        obj.highlights = self.highlights
        return obj

    def deep_copy(self):
        obj = self.__class__(self.type_name, self.editor, None, self.name, self.factor,
                        list(self.relpos), new_type=False)
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
        obj.object_type = self.object_type
        #
        obj.race = self.race
        obj.color = self.color
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.sprites = self.sprites.copy()
        obj.is_ground = self.is_ground
        #
        obj.highlights = {}
        for color in self.highlights:
            obj.highlights[color] = [i.copy() for i in self.highlights[color]]
        return obj

    def get_current_highlight(self, color):
        return self.highlights[color][self.editor.zoom_level]

    def refresh_translation_animation(self):
        if self.animation_type == ANIM_LOOP:
            delta = MapObject.refresh_translation_animation(self)
            key = DELTA_TO_KEY[delta]
            self.set_sprite_type(key)

    def set_animation_type(self, new_type):
        """new_type is either "once" or "loop"."""
        if new_type == "loop":
            self.animation_type = ANIM_LOOP
            self.get_current_img = self._free_get_current_img
            self.animation_step = 0
        elif new_type == "once":
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

    def build_highlighted_idles(self):
        frame = self.sprites_ref["idle"][0]
        self.highlights = {}
        for color in COLORS_HIGHLIGHTS:
            self.highlights[color] = []
            rgb = COLORS_HIGHLIGHTS[color]
            for z in range(len(self.editor.zoom_cell_sizes)):
                img = self.imgs_z_t[z]
                img = img[frame]
##                e = thorpy.Image(img)
                shad = thorpy.graphics.get_shadow(img, shadow_radius=HIGHLIGHT_BLUR, black=255,
                                    color_format="RGBA", alpha_factor=1.,
                                    decay_mode="exponential", color=rgb,
                                    sun_angle=45., vertical=True, angle_mode="flip",
                                    mode_value=(False, False))
                size = shad.get_rect().inflate(HIGHLIGHT_INFLATE,HIGHLIGHT_INFLATE).size
                shad = pygame.transform.smoothscale(shad, size)
                self.highlights[color].append(shad)


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
        for obj in self.cell.objects:
            if obj.name == "wood":
                return obj.name
            if obj.name == "river":
                return obj.name
        return self.cell.material.name.lower()

    def get_terrain_bonus(self):
        d = max([self.object_defense.get(o.name,1.) for o in self.cell.objects])
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