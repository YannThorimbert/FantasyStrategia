import random, thorpy
import pygame
from pygame.math import Vector2 as V2
import bisect

##from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}

ANIM_VEL = 0.2
SLOW_FIGHT_FRAME1 = 4
SLOW_FIGHT_FRAME2 = 12
STOP_TARGET_DIST_FACTOR = 0.2
NFRAMES_DIRECTIONS = 16
TIME_AFTER_FINISH = 300


SUBBATTLES = 4, 2

DFIGHT = 16
K = 4.

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
        self.final_vel = self.unit.max_dist * ANIM_VEL * (0.8 + random.random()/3.)
##        self.vel = self.final_vel / 3.
        self.vel = self.final_vel
        self.tandom = None
        self.target = None
        self.opponents = None
        self.friends = None
        self.targeted_by = []
        self.next_to_target = False
        self.time_frome_last_direction_change = 1000
        self.cannot_see = random.random()
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
        self.direction = random.choice("head","head2")
        self.refresh_sprite_type()
        self.head = self.unit.imgs_z_t[self.z][self.isprite]
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

    def stay_in_screen(self):
        pass
##        if self.pos.x > self.battle.W:
##            self.pos.x = self.battle.W
##        elif self.pos.x < 0:
##            self.pos.x = 0
##        if self.pos.y > self.battle.H:
##            self.pos.y = self.battle.H
##        elif self.pos.y < 0:
##            self.pos.y = 0



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
                    dunit = d.normalize()
                    force = dunit
##                    force = dunit / D
                    self.pos -= K * force

    def draw_and_move_notarget(self, surface):
        if len(self.opponents) != 0:
            self.direction = "idle"
            self.dxdy = (0,0)
            self.refresh_sprite_type()
        else:
            self.vel = self.final_vel / 2.
        self.direction = DELTA_TO_KEY[self.dxdy]
        frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        if self.battle.blit_this_frame:
            surface.blit(img, self.rect)
        self.pos.x += self.vel*self.dxdy[0]
        self.pos.y += self.vel*self.dxdy[1]
        self.rect.center = self.pos

    def draw_and_move(self, surface):
##        if self.battle.fight_t == self.start_to_run:
##            self.vel = self.final_vel
        if self.target is None or self.target.dead:
            self.draw_and_move_notarget(surface)
            return
        target_pos = V2(self.target.rect.center)
        self_pos = V2(self.rect.center)
        delta = target_pos - self_pos
        self.refresh_dxdy(delta.x, delta.y)
        ########################################################################
        self.next_to_target = False
        near_target = abs(delta.x) < DFIGHT and abs(delta.y) < DFIGHT
        if near_target: #fighting
            self.next_to_target = True
            if not(self.target.target is self):
                self.find_pos_near_target()
            if self.time_frome_last_direction_change > NFRAMES_DIRECTIONS:
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
        self.stay_in_screen()
        self.rect.center = self.pos
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        if self.battle.blit_this_frame:
            surface.blit(img, self.rect)
        self.time_frome_last_direction_change += 1


#unites qui fuient si trop d'ennemis (>5)!!!!!
#+ de tetes, sang sur epees des morts et choses noires et brunes
#pas dans la neige et dans le sable ?
#cas ou terrain pas le meme dans deux units ? terrain = terrain de l'attaquant ou du defenseur ? ou plutot faire vite une map mixte ?
#GUI pendant combat puis recapitulatif fin de combat. Possibilité de fuir.

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

    def __init__(self, left=None, right=None, top=None, bottom=None,
                        center=None, zoom_level=0):
        self.blocks = []
        for u in(left,right,top,bottom,center):
            if u is not None:
                self.game = u.game
                break
        self.surface = thorpy.get_screen()
        self.W, self.H = self.surface.get_size()
        self.right = right
        self.left = left
        self.top = top
        self.bottom = bottom
        self.center = center
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

    def fight(self):
        self.prepare_battle()
        self.show()


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
        menu = thorpy.Menu(bckgr, fps=60)
        self.update_battle()
        text = thorpy.make_text("Battle starts", 70, (0,0,0))
        text.center()
        text.blit()
        pygame.display.flip()
        thorpy.interactive_pause(3.)
        menu.play()

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
                u.dead = True
                if u.target:
                    u.target.targeted_by.remove(u)
                self.f.remove(u)
                u.friends.remove(u) #u.friends is u.target.opponents
##                bisect.insort(self.deads, u)
                self.deads.append(u)
                u.direction = "die"
                u.refresh_sprite_type()
##        self.deads.sort(key=lambda x:x.pos.y)
##        print(self.deads)
        self.to_remove = []

    def update_battle(self):
        if not self.finished:
            self.update_targets()
        if self.blit_this_frame:
            self.surface.blit(self.terrain, (0,0))
            self.blit_deads()
        for u in self.f:
            u.draw_and_move(self.surface)
        if self.blit_this_frame:
            pygame.display.flip()
        #
        self.refresh_deads()
        #
        self.fight_t += 1
        if self.fight_t % SLOW_FIGHT_FRAME1 == 0:
            self.fight_frame_walk += 1
        if self.fight_t % SLOW_FIGHT_FRAME2 == 0:
            self.fight_frame_attack += 1
        if self.fight_t % self.mod_display == 0:
            self.blit_this_frame = True
        else:
            self.blit_this_frame = False
        #
        self.f.sort(key=lambda x:x.rect.bottom) #peut etre pas besoin selon systeme de cible
        if len(self.f1) == 0 or len(self.f2) == 0:
            if self.finished == 0:
                self.finished = self.fight_t
                self.finish_battle()
            elif self.fight_t - self.finished > TIME_AFTER_FINISH:
                thorpy.functions.quit_menu_func()

    def finish_battle(self):
        print("FINISH BATTLE")
        for u in self.f:
            u.target = None
            u.refresh_dxdy(random.randint(-1,1),random.randint(-1,1))
            u.direction = DELTA_TO_KEY[u.dxdy]
            u.refresh_sprite_type()

    def get_nxny(self, side):
        W,H = self.surface.get_size()
        s = self.game.me.zoom_cell_sizes[self.z]
        self.cell_size = s
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
##        positions = random.sample(disp, unit.quantity)
        for i in range(unit.quantity):
            ipos = random.randint(0,len(disp)-1)
            pos = disp.pop(ipos)
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
        self.initialize_units(disp_top, self.top)
        self.initialize_units(disp_bottom, self.bottom)
        self.initialize_units(disp_center, self.center)
##        teams = [unit.team for unit in (self.left,self.right,self.top,self.bottom) if unit]
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
        self.build_terrain()
        for u in self.f:
            u.rect.center = u.pos
        self.f.sort(key=lambda x:x.rect.bottom)

    def update_targets(self):
        for u in self.f:
            u.targeted_by = []
            u.target = None
        for u in self.f:
            ennemy = u.get_nearest_ennemy()
            if ennemy:
                if len(ennemy.targeted_by) < 10:
                    u.set_target(ennemy)
                else:
                    ennemy = u.get_busyless_ennemy()
                    if ennemy:
                        if len(ennemy.targeted_by) < 6:
                            u.set_target(ennemy)



    def build_terrain(self):
        img = self.game.me.materials["Grass"].imgs[0][0]
        W,H = self.surface.get_size()
        nx = W // self.cell_size + 1
        ny = H // self.cell_size + 1
        for x in range(nx):
            for y in range(ny):
                self.terrain.blit(img, (x*self.cell_size,y*self.cell_size))
