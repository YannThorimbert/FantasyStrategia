import random, thorpy
import pygame
from pygame.math import Vector2 as V2
import bisect

##from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}

ANIM_VEL = 0.3
SLOW_FIGHT_FRAME1 = 4
SLOW_FIGHT_FRAME2 = 12
STOP_TARGET_DIST_FACTOR = 0.2
NFRAMES_DIRECTIONS = 16

DFIGHT = 8
K = 10.

def sgn(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    return 0


#remove the assertions


class FightingUnit:

    def __init__(self, battle, unit, direction, zoom_level, pos):
        self.battle = battle
        self.unit = unit
        self.z = zoom_level
        self.rect = self.unit.imgs_z_t[self.z][0].get_rect()
        self.rect.center = pos
        self.pos = V2(pos)
        self.direction = direction
        self.vel = self.unit.max_dist * ANIM_VEL * (0.8 + random.random()/3.)
        self.target = None
        self.opponents = None
        self.friends = None
        self.targeted_by = []
        self.next_to_target = False
        self.time_frome_last_direction_change = 1000
        #
        self.frame = 0
        self.frame0 = random.randint(0,12)
        self.nframes = None
        self.isprite = None
        self.z = self.z
        self.direction = "die"
        self.refresh_sprite_type()
        self.dead_img = self.unit.imgs_z_t[self.z][self.isprite + self.nframes-1]
        if random.random() < 0.5:
            self.dead_img = pygame.transform.flip(self.dead_img, True, False)
        self.direction = "left"
        self.refresh_sprite_type()
        self.dead = False

    def __lt__(self, other):
        return self.pos.y > other.pos.y

    def __gt__(self, other):
        return self.pos.y < other.pos.y

    def __leq__(self, other):
        return self.pos.y >= other.pos.y

    def __geq__(self, other):
        return self.pos.y <= other.pos.y

    def __eq__(self, other):
        return self.pos.y == other.pos.y


    def get_nearest_ennemy(self):
        distances = []
        best_d, best_o = float("inf"), None
        dok = STOP_TARGET_DIST_FACTOR*self.battle.cell_size
        for u in self.opponents:
            d = abs(self.pos.x-u.pos.x) + abs(self.pos.y-u.pos.y)
            if d < dok:
                return u
            elif d < best_d:
                best_d, best_o = d, u
        return best_o

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
        if self.pos.x > self.battle.W:
            self.pos.x = self.battle.W
        elif self.pos.x < 0:
            self.pos.x = 0
        if self.pos.y > self.battle.H:
            self.pos.y = self.battle.H
        elif self.pos.y < 0:
            self.pos.y = 0

    def find_pos_near_target(self):
        t = self.target
        for friend in t.targeted_by:
            if not(friend is self):
                d = friend.pos - self.pos
                D = d.length()
                if D > 0:
                    dunit = d.normalize()
                    force = dunit / (1. + d.length())
                    self.pos -= K * force

    def draw_and_move(self, surface):
        if self.target.dead:
            self.find_pos_near_target()
            self.direction = "idle"
            self.refresh_sprite_type()
            frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
            frame += self.isprite
            img = self.unit.imgs_z_t[self.z][frame]
            surface.blit(img, self.rect)
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
        surface.blit(img, self.rect)
        self.time_frome_last_direction_change += 1





#accelerer batailles avec space (reduit les SLOWNESS), finir battaile avec enter (supprime fps et affichage)
#coller sang sur la map plutot que de continuer de bliter sang a chaque frame
#pas dans la neige et dans le sable
#cas ou terrain pas le meme dans deux units ? terrain = terrain de l'attaquant ou du defenseur ? ou plutot faire vite une map mixte ?
class Battle:

    def __init__(self, u1, u2, terrain, zoom_level):
        self.game = u1.game
        self.surface = thorpy.get_screen()
        self.W, self.H = self.surface.get_size()
        self.u1 = u1
        self.u2 = u2
        self.terrain = terrain
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
##        self.blood = thorpy.load_image("sprites/blood.png")
        self.blood = pygame.image.load("sprites/blood.png")
        self.background = terrain

    def fight(self):
        self.prepare_battle()
        self.show()


    def accelerate(self):
        for u in self.f:
            u.vel *= 6.


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
        menu = thorpy.Menu(bckgr, fps=60)
        menu.play()

    def update_battle(self):
        if not self.finished:
            self.update_targets()
        self.surface.blit(self.terrain, (0,0))
        for u in self.deads:
            if u.frame == 0:
                u.frame = self.fight_frame_attack
            frame = self.fight_frame_attack - u.frame
            if frame == u.nframes-1:
                r = self.blood.get_rect()
                r.center = u.rect.center
                self.terrain.blit(self.blood,r)
                self.surface.blit(u.dead_img,u.rect)
            elif frame < u.nframes:
                self.surface.blit(u.unit.imgs_z_t[u.z][frame + u.isprite],u.rect)
            else:
                r = self.blood.get_rect()
                r.center = u.rect.center
                self.surface.blit(u.dead_img,u.rect)
        for u in self.f:
            u.draw_and_move(self.surface)
        pygame.display.flip()
        #
        for u in self.to_remove:
            if not u.dead: #a single battle can add a unit twice in to_remove
                u.dead = True
                u.target.targeted_by.remove(u)
                self.f.remove(u)
                u.friends.remove(u) #u.friends is u.target.opponents
                bisect.insort(self.deads, u)
                self.deads.append(u)
                u.direction = "die"
                u.refresh_sprite_type()
        self.to_remove = []
        #
        self.fight_t += 1
        if self.fight_t % SLOW_FIGHT_FRAME1 == 0:
            self.fight_frame_walk += 1
        if self.fight_t % SLOW_FIGHT_FRAME2 == 0:
            self.fight_frame_attack += 1
        #
        self.f.sort(key=lambda x:x.rect.bottom) #peut etre pas besoin selon systeme de cible
        if len(self.f1) == 0 or len(self.f2) == 0:
            if self.finished == 0:
                self.finished = self.fight_t
            elif self.fight_t - self.finished > 100:
                thorpy.functions.quit_menu_func()


    def prepare_battle(self):
        screen = thorpy.get_screen()
        W,H = screen.get_size()
        s = self.u1.editor.zoom_cell_sizes[self.z]
        self.cell_size = s
        self.W -= self.cell_size//2
        self.H -= self.cell_size//2
        #
        max_nx = W // (2*s) - 1 - 4
        max_ny = H // s - 1
        nx = max_nx
        ny = max_ny
        # print("MAX UNITS PER TEAM", nx*ny)
        #
        n1 = self.u1.quantity
        n2 = self.u2.quantity
        assert n1 <= nx*ny and n2 <= nx*ny
        disp1, disp2 = [], []
        for x in range(nx):
            for y in range(ny):
                xpos = x*s
                ypos = y*s
                disp1.append([xpos+s,ypos+s])
                disp2.append([xpos+W-s - nx*s,ypos+s])
        #
        self.f1 = []
        positions = random.sample(disp1, n1)
        for i in range(n1):
            ipos = random.randint(0,len(disp1)-1)
            pos = disp1.pop(ipos)
            pos[0] += random.randint(0,s//3)
            pos[1] += random.randint(0,s//3)
            unit = FightingUnit(self, self.u1, "right", self.z, pos)
            self.f1.append(unit)
        #
        self.f2 = []
        positions = random.sample(disp2, n2)
        for i in range(n2):
            ipos = random.randint(0,len(disp2)-1)
            pos = disp2.pop(ipos)
            pos[0] += random.randint(0,s//3)
            pos[1] += random.randint(0,s//3)
            unit = FightingUnit(self, self.u2, "left", self.z, pos)
            self.f2.append(unit)
        for u1 in self.f1:
            u1.opponents = self.f2
            u1.friends = self.f1
        for u2 in self.f2:
            u2.opponents = self.f1
            u2.friends = self.f2
        self.update_targets()
        self.f = self.f1 + self.f2
##        self.build_terrain()

    def update_targets(self):
        for u in self.f:
            u.targeted_by = []
            u.target = None
        for u in self.f:
            ennemy = u.get_nearest_ennemy()
##            ennemy = u.get_nearest_free_ennemy()
            u.target = ennemy
            ennemy.targeted_by.append(u)

    def build_terrain(self):
        img = self.game.me.materials["Grass"].imgs[0][0]
        W,H = self.surface.get_size()
        nx = W // self.cell_size + 1
        ny = H // self.cell_size + 1
        for x in range(nx):
            for y in range(ny):
                self.terrain.blit(img, (x*self.cell_size,y*self.cell_size))

##    def circles(self):
##        fights = []
##        for u1 in self.f1:
##            if u1.next_to_target:
##                if u1.target.target is u1:
##                    fights.append((u1,u2))
##        for u1,u2 in fights:
##
##
##            L = len(u2.targeted_by)
##            delta_angle = 360. / L
##            for u2 in u1.targeted_by:





