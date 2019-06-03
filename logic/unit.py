import random
import pygame, thorpy
from PyWorld2D.mapobjects.objects import MapObject
import PyWorld2D.constants as const



SPRITES_KEYS = ["idle", "right", "left", "down", "up", "lattack", "rattack", "die", "head"]
COLORS_HIGHLIGHTS = {"red":(255,0,0), "yellow":(255,255,0), "blue":(0,0,255)}
HIGHLIGHT_BLUR = 3
HIGHLIGHT_INFLATE = 10

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}

COLORS = {"blue":((160,195,210),(110,160,185),(76,95,128)), #SRC_COLOR
          "red":((255,175,140),(230,140,90),(175,75,56)),
          "green":((195,255,160),(160,230,110),(95,175,76)),
          "black":((130,)*3,(90,)*3,(75,)*3)}

class Unit(MapObject):

    @staticmethod
    def get_saved_attributes():
        return MapObject.get_saved_attributes() + ["team"]

    def __init__(self, type_name, editor, sprites, name=None, factor=1., relpos=(0,0),
                    build=True, new_type=True):
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
        MapObject.__init__(self, editor, imgs, type_name, factor, relpos, build, new_type)
        self.type_name = type_name
        self.cost = None
        self.max_dist = None
        self.race = None
        self.game = None
        #
        self.walk_img = {}
        self.set_frame_refresh_type(2) #type fast
        self.vel = 0.07
        self.current_isprite = 0
        self.team = None
        self.attack_range = None
        self.help_range = None




    def _spawn_possible_destinations(self, x, y, tot_cost, path_to_here, score):
        for dx,dy in DELTAS:
            cx, cy = x+dx, y+dy #next cell
            next_cell = self.editor.lm.get_cell_at(cx,cy)
            if next_cell:
                if next_cell.unit:
                    if next_cell.unit.team != self.team:
                        continue
                no_key_value = float("inf"), None
                best_score, best_path = score.get((cx,cy), no_key_value)
                #compute the cost of the current path ##########################
                for obj in next_cell.objects:
                    if not isinstance(obj, Unit):
                        this_tot_cost = self.cost[obj.name]
                        break
                else: #if break is never reached
                    this_tot_cost = self.cost[next_cell.material.name]
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


    def copy(self):
        """The copy references the same images as the original !"""
        self.ncopies += 1
        obj = Unit(self.type_name, self.editor, None, self.name, self.factor,
                        list(self.relpos), new_type=False)
        obj.original_imgs = self.original_imgs
        obj.nframes = self.nframes
        obj.imgs_z_t = self.imgs_z_t
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.object_type = self.object_type
        obj.quantity = self.quantity
        obj.fns = self.fns
        #
        obj.cost = self.cost.copy()
        obj.max_dist = self.max_dist
        obj.race = self.race
        obj.vel = self.vel
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.sprites_ref = self.sprites_ref.copy()
        obj.is_ground = self.is_ground
        obj.highlights = self.highlights
        obj.team = self.team
        obj.help_range = self.help_range
        obj.attack_range = self.attack_range
        return obj

    def deep_copy(self):
        obj = Unit(self.type_name, self.editor, None, self.name, self.factor,
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
        obj.cost = self.cost.copy()
        obj.max_dist = self.max_dist
        obj.race = self.race
        obj.vel = self.vel
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.sprites_ref = self.sprites_ref.copy()
        obj.is_ground = self.is_ground
        obj.team = self.team
        obj.help_range = self.help_range
        obj.attack_range = self.attack_range
        obj.highlights = {}
        for color in self.highlights:
            obj.highlights[color] = [i.copy() for i in self.highlights[color]]
        return obj

    def get_current_highlight(self, color):
        return self.highlights[color][self.editor.zoom_level]

    def get_current_img(self):
        frame = self.get_current_frame()+self.current_isprite
        return self.imgs_z_t[self.editor.zoom_level][frame]

    def set_sprite_type(self, key):
        i,n,t = self.sprites_ref[key]
        self.current_isprite = i
        self.nframes = n
        self.set_frame_refresh_type(t)

    def refresh_translation_animation(self):
        delta = MapObject.refresh_translation_animation(self)
        key = DELTA_TO_KEY[delta]
        self.set_sprite_type(key)

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

    def get_fight_result(self, other): #-1, 0, 1
        if random.random() < 1e-2:
            return random.choice([-1,1])
        return 0



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

def load_sprites(fn, colors="blue", h=const.FAST, v=const.FAST, i=const.SLOW):
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
