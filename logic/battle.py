import random, thorpy
import numpy as np
import pygame
from pygame.math import Vector2 as V2
import bisect

##from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}

ANIM_VEL = 1.5
SLOW_FIGHT_FRAME1 = 4
SLOW_FIGHT_FRAME2 = 12
STOP_TARGET_DIST_FACTOR = 0.2
NFRAMES_DIRECTIONS = 16
TIME_AFTER_FINISH = 1000
BATTLE_DURATION = 1000
DEFENSE_START_RUNNING = BATTLE_DURATION + TIME_AFTER_FINISH + 1 #for the moment, I deactivate this feature

MAX_TARGETED_BY = 10
MAX_TARGETED_BY2 = 6

SUMMARY_LIFEBAR_SIZE = (150,25)

P_DEAD_SOUND = 0.5
P_HIT_SOUND = 0.04

DFIGHT = 16
K = 2.

def sgn(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    return 0



ID = 0

class FightingUnit:

    def __init__(self, battle, unit, direction, zoom_level, pos):
        self.battle = battle
        self.unit = unit
        self.z = zoom_level
        self.rect = self.unit.imgs_z_t[self.z][0].get_rect()
        self.rect.center = pos
        self.pos = V2(pos)
        self.init_pos = V2(pos)
        self.direction = direction
##        self.final_vel = self.unit.max_dist * ANIM_VEL * (0.8 + random.random()/3.)
        self.final_vel = ANIM_VEL * (0.8 + random.random()/3.)
        self.vel = self.final_vel
        self.tandom = None
        self.target = None
        self.opponents = None
        self.friends = None
        self.targeted_by = []
        # self.next_to_target = False
        self.time_frome_last_direction_change = 1000
        self.cannot_see = random.random()
        self.final_stage = False
        #
        self.dxdy = 0,0
        self.start_to_run = random.randint(0, 1000)
        self.frame = 0
        self.frame0 = random.randint(0,12)
        self.nframes = None
        self.isprite = None
        self.z = self.z
        self.direction = "die"
        self.refresh_sprite_type()
        self.dead_img = self.unit.imgs_z_t[self.z][self.isprite + self.nframes-1]
        self.direction = "head"
        self.refresh_sprite_type()
        irand = random.randint(0, self.nframes-1)
        self.head = self.unit.imgs_z_t[self.z][self.isprite+irand]
        dhx = random.randint(self.battle.cell_size//2, self.battle.cell_size)
        dhy = random.choice([-1,1]) * random.randint(0,self.battle.cell_size//4)
        if random.random() < 0.5:
            self.dead_img = pygame.transform.flip(self.dead_img, True, False)
            dhx *= -1
        self.delta_head = (dhx,dhy)
        self.direction = "left"
        self.refresh_sprite_type()
        self.dead = False
        global ID
        self.id = ID
        ID += 1

    def __lt__(self, other):
        return self.pos.y < other.pos.y

    def __gt__(self, other):
        return self.pos.y > other.pos.y

    def __leq__(self, other):
        return self.pos.y <= other.pos.y

    def __geq__(self, other):
        return self.pos.y >= other.pos.y

##    def __eq__(self, other):
##        return self.pos.y == other.pos.y

##    def __hash__(self):
##        return hash(self.id)


    def get_nearest_ennemy(self):
        best_d, best_o = float("inf"), None
        dok = STOP_TARGET_DIST_FACTOR*self.battle.cell_size
        L = int(self.cannot_see * len(self.opponents))
        if L == 0 and self.opponents:
            L = 1
        for i in range(L):
            u = self.opponents[i]
            d = abs(self.pos.x-u.pos.x) + abs(self.pos.y-u.pos.y)
            if d < dok:
                return u
            elif d < best_d:
                best_d, best_o = d, u
        return best_o

    def get_busyless_ennemy(self):
        best_d, best_o = float("inf"), None
        for u in self.opponents:
            d = len(u.targeted_by)
            if d < best_d:
                best_d, best_o = d, u
        return best_o

##    def get_furthest_ennemy(self):
##        distances = []
##        best_d, best_o = (float("inf"),float("inf")), None
##        dok = STOP_TARGET_DIST_FACTOR_FAR*self.battle.cell_size
##        dok = (dok,dok)
##        for u in self.opponents:
##            delta = abs(self.pos.x-u.pos.x), abs(self.pos.y-u.pos.y)
##            if delta < dok:
##                return u
##            elif delta < best_d:
##                best_d, best_o = delta, u
##        return best_o

##    def get_ennemy(self):
##        if self.strategy == 0:
##            return self.get_nearest_ennemy()
##        else:
##            return self.get_furthest_ennemy()

##    def get_ennemy(self):
##        return self.get_nearest_ennemy()

    def refresh_sprite_type(self):
        i,n,t = self.unit.sprites_ref[self.direction]
        self.isprite = i
        self.nframes = n
        self.frame = 0

    def refresh_dxdy(self, rdx, rdy):
        #must not stay at rest
        adx = abs(rdx)
        ady = abs(rdy)
        if adx > ady: #will move horizontally
            if rdx > 0:
                self.dxdy = 1,0
            else:
                self.dxdy = -1,0
        else: #will move vertically
            if rdy > 0:
                self.dxdy = 0,1
            else:
                self.dxdy = 0,-1


    def set_target(self, other):
        self.target = other
        other.targeted_by.append(self)

    def find_pos_near_target(self):
        t = self.target
        for friend in t.targeted_by:
            if not(friend is self):
                d = friend.pos - self.pos
                D = d.length()
                if 0 < D <= self.battle.cell_size:
                    force = d / D
                    self.pos -= K * force

    def draw_and_move_notarget(self):
        if self.battle.fight_t < BATTLE_DURATION:
            if len(self.opponents) > 0:
                self.direction = "idle"
                self.dxdy = (0,0)
                self.refresh_sprite_type()
                self.vel = 0.
                frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
            else:
                delta = self.update_dest_end()
                frame = (self.frame0 + self.battle.fight_frame_walk)%self.nframes
        else:
            delta = self.update_dest_end()
            dl = delta.length()
            if dl < self.battle.cell_size:
                self.direction = "idle"
                self.dxdy = (0,0)
                self.refresh_sprite_type()
                self.vel = 0.
                frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
            else:
                frame = (self.frame0 + self.battle.fight_frame_walk)%self.nframes
        #
        if self.battle.blit_this_frame:
            frame += self.isprite
            img = self.unit.imgs_z_t[self.z][frame]
            self.blit(img)
        self.pos.x += self.vel*self.dxdy[0]
        self.pos.y += self.vel*self.dxdy[1]
        self.rect.center = self.pos

    def draw_and_move(self):
        if self.battle.fight_t == self.start_to_run:
            self.vel = self.final_vel
        if self.target is None or self.target.dead:
            self.draw_and_move_notarget()
            self.time_frome_last_direction_change += 1
            return
        target_pos = V2(self.target.rect.center)
        self_pos = V2(self.rect.center)
        delta = target_pos - self_pos
        self.refresh_dxdy(delta.x, delta.y)
        ########################################################################
        # self.next_to_target = False
        near_target = abs(delta.x) < DFIGHT and abs(delta.y) < DFIGHT
        if near_target: #fighting
            if self.battle.game.hit_sounds and random.random() < P_HIT_SOUND:
                random.choice(self.battle.game.hit_sounds).play()
            # self.next_to_target = True
            if self.time_frome_last_direction_change > NFRAMES_DIRECTIONS:
                if not(self.target.target is self):
                    self.find_pos_near_target()
                self.direction = DELTA_TO_KEY_A[self.dxdy]
                self.refresh_sprite_type()
                self.time_frome_last_direction_change = 0
            frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
            if not self.target.dead and not self.dead:
                result = self.unit.get_fight_result(self.target)
                if result < 0:
                    self.battle.to_remove.append(self)
                elif result > 0:
                    self.battle.to_remove.append(self.target)
        else: #walking
            if self.time_frome_last_direction_change > NFRAMES_DIRECTIONS:
                self.direction = DELTA_TO_KEY[self.dxdy]
                self.refresh_sprite_type()
                self.time_frome_last_direction_change = 0
            frame = (self.frame0 + self.battle.fight_frame_walk)%self.nframes
            self.pos.x += self.vel*self.dxdy[0]
            self.pos.y += self.vel*self.dxdy[1]
        self.rect.center = self.pos
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        self.blit(img)
        self.time_frome_last_direction_change += 1

    def update_dest_end(self):
        delta = self.init_pos - self.pos
        self.refresh_dxdy(delta.x, delta.y)
        if self.time_frome_last_direction_change > NFRAMES_DIRECTIONS:
            self.direction = DELTA_TO_KEY[self.dxdy]
            self.refresh_sprite_type()
            self.time_frome_last_direction_change = 0
        return delta

    def blit(self, img):
         if self.battle.blit_this_frame:
            if self.battle.show_footprints:
                if self.battle.fight_frame_walk % 4 == 0:
                    cx,cy = self.battle.get_cell_coord(self.pos[0], self.pos[1])
                    if self.battle.is_footprint[cx,cy]:
                        x = self.rect.centerx
                        y = self.rect.bottom - 4
                        self.battle.terrain.blit(self.unit.footprint, (x,y))
            self.battle.surface.blit(img, self.rect)
            if self.battle.show_splash:
                cx,cy = self.battle.get_cell_coord(self.pos[0], self.pos[1])
                if self.battle.is_splash[cx,cy]:
                    self.battle.surface.blit(self.battle.splash, self.rect.move(0,-4).bottomleft)






class Battle:
    """The rules for the engagements are the following.

        A) The defending unit can receive help from ONE friend unit, only if the
        latter is immediately next to the defending unit (distance 1).

        B) Any attacking team unit can participate to the assault, provided that
        it is immediately next to the defending unit (distance 1).

        As a consequence of A) and B), distance attacks are only possible
        from one unit to one other unit. Unit with long range attack can
        participate to multi-battles only if they are able to fight at distance 1.

        Another consequence of A) and B) is that the maximum number of different
        units that can be involved in a battle is 5.

    """

    def __init__(self, game, units, defender, zoom_level=0):
        self.defender = defender
        units = get_units_dict_from_list(units)
        self.blocks = []
        self.game = game
        self.surface = thorpy.get_screen()
        self.W, self.H = self.surface.get_size()
        print("BATTLE", units)
        self.right = units.get("right")
        self.left = units.get("left")
        self.up = units.get("up")
        self.down = units.get("down")
        self.center = units.get("center")
        self.terrain = pygame.Surface(self.surface.get_size())
        self.z = zoom_level
        self.cell_size = None
        self.f1 = []
        self.f2 = []
        self.f = []
        self.deads = []
        self.to_remove = []
        self.fights = []
        self.fight_t = 0
        self.fight_frame_walk = 0
        self.fight_frame_attack = 0
        self.finished = 0
        self.blood = pygame.image.load("sprites/blood.png")
        self.background = None
        self.mod_display = 1
        self.blit_this_frame = True
        self.show_footprints = True
        self.splashes = [pygame.image.load("sprites/splash.png")]
        self.splashes.append(pygame.transform.flip(self.splashes[0], True, False))
        self.splash = self.splashes[0]
        self.show_splash = True
        self.is_splash = None
        self.is_footprint = None
        self.nx = None
        self.ny = None
        self.walk_sounds = []
        self.screams = []
        self.text_finish = thorpy.Element("Press enter to finish battle")
        self.text_finish.set_font_size(70)
        self.text_finish.set_main_color((255,255,255,100))
        self.text_finish.scale_to_title()
        self.text_finish.center()
        self.before_f1 = None
        self.before_f2 = None

    def press_enter(self):
        if self.finished:
            self.fight_t = 100000000000

    def fight(self):
        self.prepare_battle()
        self.show()
        self.show_summary()

    def accelerate(self):
        self.mod_display = 10
        thorpy.get_current_menu().fps = 500

    def slow(self):
        self.mod_display = 1
        thorpy.get_current_menu().fps = 60


    def show(self):
        bckgr = thorpy.Ghost()
        reac = thorpy.ConstantReaction(thorpy.constants.THORPY_EVENT,
                                    self.update_battle,
                                    {"id":thorpy.constants.EVENT_TIME})
        bckgr.add_reaction(reac)
        #
        reac = thorpy.ConstantReaction(pygame.KEYDOWN,
                                        self.accelerate,
                                        {"key":pygame.K_SPACE})
        bckgr.add_reaction(reac)
        reac = thorpy.ConstantReaction(pygame.KEYUP,
                                        self.slow,
                                        {"key":pygame.K_SPACE})
        bckgr.add_reaction(reac)
        reac = thorpy.ConstantReaction(pygame.KEYUP,
                                        self.press_enter,
                                        {"key":pygame.K_RETURN})
        bckgr.add_reaction(reac)
        #
        menu = thorpy.Menu(bckgr, fps=60)
        self.update_battle()
        text = thorpy.make_text("Battle starts", 70, (0,0,0))
        text.center()
        text.blit()
        pygame.display.flip()
##        thorpy.interactive_pause(3.)
        #######################################################################
        self.game.outdoor_sound.stop()
        self.add_walk_sounds()
        menu.play()
        for s in self.walk_sounds:
            s.stop()
        self.game.outdoor_sound.play(-1)



    def add_walk_sounds(self):
        counter = 0
        max_n = min(10, len(self.f)//7 + 1)
        for s in self.game.walk_sounds:
            if counter < max_n:
                pygame.time.wait(random.randint(10,100))
                s.play(-1)
                self.walk_sounds.append(s)
                counter += 1

    def refresh_walk_sounds(self):
        L = len([u for u in self.f if u.vel > 0.])
        if L == 0:
            for s in self.walk_sounds:
                s.stop()
            self.walk_sounds = []
            return
        max_n = min(10, L//7 + 1)
        while len(self.walk_sounds) > max_n:
            s = self.walk_sounds.pop()
            s.stop()


    def blit_deads(self):
         for u in self.deads:
            if u.frame == 0:
                u.frame = self.fight_frame_attack
            frame = self.fight_frame_attack - u.frame
            if frame == u.nframes-1:
                r = self.blood.get_rect()
                r.center = u.rect.center
                r.y += self.cell_size//2
                self.terrain.blit(self.blood,r)
                self.surface.blit(u.dead_img,u.rect)
                self.terrain.blit(u.head, u.rect.move(u.delta_head))
            elif frame < u.nframes:
                self.surface.blit(u.unit.imgs_z_t[u.z][frame + u.isprite],u.rect)
            else:
                r = self.blood.get_rect()
                r.center = u.rect.center
                self.surface.blit(u.dead_img,u.rect)

    def refresh_deads(self):
        for u in self.to_remove:
            if not u.dead:
                if self.game.death_sounds and random.random() < P_DEAD_SOUND:
                    random.choice(self.game.death_sounds).play()
                u.dead = True
                if u.target:
                    u.target.targeted_by.remove(u)
                self.f.remove(u)
                u.friends.remove(u) #u.friends is u.target.opponents
                self.deads.append(u)
                u.direction = "die"
                u.refresh_sprite_type()
        self.to_remove = []

    def update_battle(self):
        if not self.finished:
            self.update_targets()
        if self.blit_this_frame:
            self.surface.blit(self.terrain, (0,0))
            self.blit_deads()
        for u in self.f:
            u.draw_and_move()
        if self.blit_this_frame:
            if self.finished:
                self.text_finish.blit()
            pygame.display.flip()
        #
        self.refresh_deads()
        #
        self.fight_t += 1
        if self.fight_t % SLOW_FIGHT_FRAME1 == 0:
            self.fight_frame_walk += 1
            self.splash = self.splashes[self.fight_frame_walk%2]
        if self.fight_t % SLOW_FIGHT_FRAME2 == 0:
            self.fight_frame_attack += 1
            self.refresh_walk_sounds()
        if self.fight_t % self.mod_display == 0:
            self.blit_this_frame = True
        else:
            self.blit_this_frame = False
        #
        self.f.sort(key=lambda x:x.rect.bottom) #peut etre pas besoin selon systeme de cible
        extermination = len(self.f1) == 0 or len(self.f2) == 0

        if extermination or self.fight_t > BATTLE_DURATION:
            if self.finished == 0:
                self.finished = self.fight_t
                self.finish_battle()
            elif self.fight_t - self.finished > TIME_AFTER_FINISH:
                thorpy.functions.quit_menu_func()
##        if self.fight_t % 20 == 0:
##            print(self.fight_t)

    def finish_battle(self):
        print("FINISH BATTLE")
        for u in self.f:
            u.target = None
            u.update_dest_end()
            u.vel = u.final_vel


    def get_nxny(self, side):
        W,H = self.surface.get_size()
        s = self.game.me.zoom_cell_sizes[self.z]
        self.cell_size = s
        self.nx = W//self.cell_size
        self.ny = H//self.cell_size
##        self.W -= self.cell_size//2
##        self.H -= self.cell_size//2
        if side == "left" or side == "right":
            max_nx = W // (2*s) - 1 - 6
            max_ny = H // s - 1 - 8
        elif side == "bottom" or side == "top":
            max_ny = H // (2*s) - 1 - 6
            max_nx = W // s - 1 - 2
        elif side == "center":
            max_nx = W // (3*s) + 2
            max_ny = H // (3*s) + 2
        else:
            assert False
        return max_nx, max_ny

    def get_disp_poses_x(self, side):
        nx,ny = self.get_nxny(side)
        s = self.game.me.zoom_cell_sizes[self.z]
        space_x = nx*s
        space_y = ny*s
        dy = (self.H - space_y) // 2
        disp = []
        if side == "right":
            dx = self.W - space_x
        else:
            dx = s//2
        for x in range(nx):
            xpos = x*s
            for y in range(ny):
                ypos = y*s
                disp.append([xpos+dx,ypos+s+dy])
        return disp

    def get_disp_poses_y(self,side):
        nx,ny= self.get_nxny(side)
        s = self.game.me.zoom_cell_sizes[self.z]
        space_y = ny*s
        space_x = nx*s
        dx = (self.W-space_x) // 2
        disp = []
        if side == "bottom":
            dy = self.H - space_y
        else:
            dy = s//2
        for x in range(nx):
            xpos = x*s
            for y in range(ny):
                ypos = y*s
                disp.append([xpos+dx, ypos+dy])
        return disp

    def get_disp_poses_c(self):
        nx,ny = self.get_nxny("center")
        s = self.game.me.zoom_cell_sizes[self.z]
        disp = []
        space_y = ny*s
        space_x = nx*s
        dx = (self.W-space_x) // 2
        dy = (self.H-space_y) // 2
        for x in range(nx):
            for y in range(ny):
                xpos = x*s
                ypos = y*s
                disp.append([xpos+dx, ypos+dy])
        return disp


    def initialize_units(self, disp, unit):
        s = self.game.me.zoom_cell_sizes[self.z]
        if unit is None:
            return
        if unit.team == 1:
            population = self.f1
        elif unit.team == 2:
            population = self.f2
        positions = random.sample(disp, unit.quantity)
        for i in range(unit.quantity):
            ipos = random.randint(0,len(disp)-1)
##            pos = disp.pop(ipos)
            pos = list(positions[i])
            pos[0] += random.randint(0,s//3)
            pos[1] += random.randint(0,s//3)
            u = FightingUnit(self, unit, "right", self.z, pos)
            population.append(u)

    def prepare_battle(self):
        s = self.game.me.zoom_cell_sizes[self.z]
##        assert n1 <= nx*ny and n2 <= nx*ny
        disp_left = self.get_disp_poses_x("left")
        disp_right = self.get_disp_poses_x("right")
        disp_top = self.get_disp_poses_y("top")
        disp_bottom = self.get_disp_poses_y("bottom")
        disp_center = self.get_disp_poses_c()
        #
        self.f1 = []
        self.f2 = []
        #
        self.initialize_units(disp_left, self.left)
        self.initialize_units(disp_right, self.right)
        self.initialize_units(disp_top, self.up)
        self.initialize_units(disp_bottom, self.down)
        self.initialize_units(disp_center, self.center)
##        teams = [unit.team for unit in (self.left,self.right,self.up,self.down) if unit]
##        if len(teams) > 1 and len(set(teams)) == 1:
##            initialize_units(disp_center, self.center)
        for u1 in self.f1:
            u1.opponents = self.f2
            u1.friends = self.f1
        for u2 in self.f2:
            u2.opponents = self.f1
            u2.friends = self.f2
        self.update_targets()
        self.f = self.f1 + self.f2
        self.is_footprint = np.zeros((self.nx, self.ny), dtype=bool)
        self.is_splash = np.zeros((self.nx, self.ny), dtype=bool)
        self.build_base_terrain()
        self.build_terrain(disp_left, self.left)
        self.build_terrain(disp_right, self.right)
        self.build_terrain(disp_top, self.up)
        self.build_terrain(disp_bottom, self.down)
        self.build_terrain(disp_center, self.center)
        for u in self.f:
            u.rect.center = u.pos
            if u.unit is self.defender:
                u.start_to_run = DEFENSE_START_RUNNING
                u.vel = u.final_vel / 2.
        self.f.sort(key=lambda x:x.rect.bottom)
        #
##        self.before_f1 = len(self.f1), self.f1[0].unit
##        self.before_f2 = len(self.f2), self.f2[0].unit


    def update_targets(self):
        for u in self.f:
            u.targeted_by = []
            u.target = None
            if len(u.opponents) < 10 and not u.final_stage:
                u.cannot_see = random.random() * 0.2
                u.final_stage = True
        for u in self.f:
            ennemy = u.get_nearest_ennemy()
            if ennemy:
                u.set_target(ennemy)



    def build_terrain(self, disp, unit):
        if not unit:
            return
        img, splash, footprint = get_img(unit.cell, self.z)
        for x,y in disp:
            self.terrain.blit(img, (x,y))
            x,y = self.get_cell_coord(x,y)
            self.is_splash[x,y] = splash
            self.is_footprint[x,y] = footprint

    def build_base_terrain(self):
        W,H = self.surface.get_size()
        nx = W // self.cell_size + 1
        ny = H // self.cell_size + 1
        cell = pygame.Rect(0, 0, self.cell_size, self.cell_size)
        for x in range(nx):
            cell.x = x*self.cell_size
            for y in range(ny):
                cell.y = y*self.cell_size
                self.build_unknown_terrain(cell)

    def build_unknown_terrain(self, cell):
        def choose(units_order):
            for u in units_order:
                if u is not None:
                    return u
            assert False
        if cell.x < self.W//3:
            if cell.y < self.H//3:
                u = choose((self.up,self.left,self.center,self.right,self.down))
            elif cell.y > 2*self.H//3:
                u = choose((self.down,self.left,self.center,self.right,self.up))
            else:
                u = choose((self.left,self.center,self.up,self.down,self.right))
        elif cell.x > 2*self.W//3:
            if cell.y < self.H//3:
                u = choose((self.up,self.right,self.center,self.left,self.down))
            elif cell.y > 2*self.H//3:
                u = choose((self.down,self.right,self.center,self.left,self.up))
            else:
                u = choose((self.right,self.center,self.up,self.down,self.left))
        else:
            if cell.y < self.H//3:
                u = choose((self.up,self.center,self.left,self.right,self.down))
            elif cell.y > 2*self.H//3:
                u = choose((self.down,self.center,self.left,self.right,self.up))
            else:
                u = choose((self.center,self.up,self.down,self.left,self.right))
##        img = u.cell.material.imgs[self.z][0]
        img, splash, footprint = get_img(u.cell, self.z)
        self.terrain.blit(img, cell.topleft)
        x,y = self.get_cell_coord(cell.x,cell.y)
        self.is_splash[x,y] = splash
        self.is_footprint[x,y] = footprint

    def get_cell_coord(self, x, y):
        return int((x * self.nx) // self.W), int((y * self.ny) // self.H)

    def refresh_unit_quantities(self, side):
        after = {}
        uside = getattr(self, side)
        for u in self.deads:
            if u.unit is uside:
                uside.quantity -= 1


    def show_summary(self):
        #
        e1 = thorpy.make_text("Battle summary", 36)
        e2 = thorpy.Line(2*e1.get_rect().width // 3, "h")
        els = {}
        names = {"left":"west", "right":"east", "up":"north", "down":"south", "center":"center"}
        for side in ("left", "center", "right", "up", "down"):
            u = getattr(self, side)
            if u:
                engaged = thorpy.LifeBar("Before battle: "+str(u.quantity),
                                            size=SUMMARY_LIFEBAR_SIZE)
                before = u.quantity
                self.refresh_unit_quantities(side)
                dead = thorpy.LifeBar("After battle: "+str(u.quantity),
                                        size=SUMMARY_LIFEBAR_SIZE)
                dead.set_life(u.quantity/before)
                #
                side = names[side]
                eside = thorpy.make_text(side.capitalize()+" unit")
                line = thorpy.Line(eside.get_rect().width, "h")
                race = thorpy.make_text(u.race.name)
                utype = thorpy.make_text(u.name.capitalize())
                race_type = thorpy.make_group([race, utype])
                els[side] = thorpy.Box([eside,line,race_type,engaged,dead])
            else:
                side = names[side]
                els[side] = thorpy.Box([thorpy.make_text("No "+side+" unit")])
        group_center = thorpy.make_group([els["west"], els["center"], els["east"]])
        e = thorpy.make_ok_box([e1,e2,els["north"],group_center,els["south"]])
        e.set_main_color((255,255,255,100))
        e.center()
        b = self.game.me.draw()
        pygame.display.flip()
        thorpy.launch_blocking(e)


def get_units_dict_from_list(units):
    coords = [u.cell.coord for u in units]
    assert 1 < len(coords) <= 5
    neighbours = {}
    for u in units:
        x,y = u.cell.coord
        neighbours[u] = []
        for dx,dy in DELTAS:
            if (x+dx,y+dy) in coords:
                neighbours[u].append((dx,dy))
    #now choose the units with the largest amount of neighbours
    candidates = [(len(neighbours[u]),units.index(u),u) for u in neighbours]
    center_unit = max(candidates)[-1]
    game = center_unit.game
    x,y = center_unit.cell.coord
    #build the relative dict
    relative_dict = {}
    for dx,dy in neighbours[center_unit]:
        key = DELTA_TO_KEY[(dx,dy)]
        other = game.get_unit_at(x+dx,y+dy)
        relative_dict[key] = other
    #now build the final dict
    if len(coords) == 2:
        assert len(relative_dict) == 1
        only_key = list(relative_dict.keys())[0]
        dx,dy = KEY_TO_DELTA[only_key]
        otherkey = DELTA_TO_KEY[(-dx,-dy)]
        relative_dict[otherkey] = center_unit
    else:
        relative_dict["center"] = center_unit
    return relative_dict


def get_img(cell, z):
    splash = False
    footprint = False
    for obj in cell.objects:
        if obj.name == "river":
            img = obj.imgs_z_t[z][0]
            splash = True
            break
    else:
        img = cell.material.imgs[z][0]
        n = cell.material.name.lower()
        if "sand" in n or "snow" in n:
            footprint = True
    return img, splash, footprint
