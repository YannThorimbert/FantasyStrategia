import random, thorpy
import pygame


KEY_TO_DELTA = {"right":(1,0), "left":(-1,0), "down":(0,1), "up":(0,-1)}
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
ANIM_VEL = 0.1
SLOW_FIGHT_FRAME = 4
MOD_CHANGE_TARGET = 10

def sgn(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1
    return 0


class FightingUnit:

    def __init__(self, battle, unit, direction, zoom_level, pos):
        self.battle = battle
        self.unit = unit
        self.z = zoom_level
        self.rect = self.unit.imgs_z_t[self.z][0].get_rect()
        self.rect.center = pos
        self.pos = self.rect.center
        self.direction = direction
        self.vel = self.unit.max_dist * ANIM_VEL
        self.target = None
        #
        self.frame0 = random.randint(0,12)
        self.nframes = None
        self.isprite = None
        self.z = self.z
        self.set_sprite_type("left")
        self.dead = False
        self.dead_img = pygame.Surface(self.rect.size)
        self.dead_img.fill((255,0,0))

    def set_sprite_type(self, key):
        i,n,t = self.unit.sprites_ref[key]
        self.isprite = i
        self.nframes = n
        # self.set_frame_refresh_type(t)


    def draw_and_move(self, surface):
        if self.dead:
            return
        frame = (self.frame0 + self.unit.game.fight_frame)%self.nframes
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        surface.blit(img, self.rect)
        #
        rdx = self.target.pos[0] - self.pos[0]
        rdy = self.target.pos[1] - self.pos[1]
        if abs(rdx) < 30 and abs(rdy) < 30:
            self.set_sprite_type("lattack")
            if self.unit.team < self.target.unit.team: #prevent doublons
                self.battle.fights.append((self, self.target))
            return
        else:
            dx = sgn(rdx)
            dy = sgn(rdy)
            if dx:
                self.direction = DELTA_TO_KEY[(dx,0)]
            elif dy:
                self.direction = DELTA_TO_KEY[(0,dy)]
            dx, dy =  KEY_TO_DELTA[self.direction]
            self.set_sprite_type(self.direction)
            #
            self.pos = (self.pos[0]+self.vel*dx, self.pos[1]+self.vel*dy)
            self.rect.center = self.pos





class Battle:

    def __init__(self, u1, u2, terrain, zoom_level):
        self.game = u1.game
        self.surface = thorpy.get_screen()
        self.u1 = u1
        self.u2 = u2
        self.terrain = terrain
        self.z = zoom_level
        self.f1 = []
        self.f2 = []
        self.f = []
        self.deads = []
        self.fights = []
        self.prepare_battle()
        self.show()

    def show(self):
        bckgr = thorpy.Ghost()
        reac = thorpy.ConstantReaction(thorpy.constants.THORPY_EVENT,
                                    self.update_battle,
                                    {"id":thorpy.constants.EVENT_TIME})
        bckgr.add_reaction(reac)
        menu = thorpy.Menu(bckgr, fps=60)
        menu.play()

    def update_battle(self):
        self.surface.fill((255,255,255))
        for u in self.deads:
            self.surface.blit(u.dead_img, u.rect)
        for u in self.f:
            u.draw_and_move(self.surface)
        self.game.fight_t += 1
        if self.game.fight_t % SLOW_FIGHT_FRAME == 0:
            self.game.fight_frame += 1
        pygame.display.flip()
        #
        self.f.sort(key=lambda x:x.pos[1]) #peut etre pas besoin selon systeme de cible
        if self.game.fight_t % MOD_CHANGE_TARGET == 0:
            self.update_target()
        to_remove, deads = self.game.update_fights(self.fights)
        self.deads += deads
        for i in to_remove[::-1]:
            print("DEAD",i)
            self.fights.pop(i)
        for u in deads:
            if u in self.f1:
                self.f1.remove(u)
            elif u in self.f2:
                self.f2.remove(u)
            # self.f.remove(u)

    def update_target(self): #trick : faire un break si distance < 2*s
        for u1 in self.f1:
            x,y = u1.pos
            distances = []
            distances = [(abs(x-u2.pos[0]) + abs(y-u2.pos[1]),u2) for u2 in self.f2]
            distances.sort(key=lambda x:x[0])
            u1.target = distances[0][1]
        for u2 in self.f2:
            x,y = u2.pos
            distances = []
            distances = [(abs(x-u1.pos[0]) + abs(y-u1.pos[1]),u1) for u1 in self.f1]
            distances.sort(key=lambda x:x[0])
            u2.target = distances[0][1]


    def prepare_battle(self):
        screen = thorpy.get_screen()
        W,H = screen.get_size()
        s = self.u1.editor.zoom_cell_sizes[self.z]
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
        self.update_target()
        self.f = self.f1 + self.f2
