import random, thorpy
import pygame

##from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}
DELTA_TO_KEY_SLOT = {(-dx,-dy):DELTA_TO_KEY_A[(dx,dy)] for dx,dy in DELTA_TO_KEY_A}

ANIM_VEL = 0.2
SLOW_FIGHT_FRAME1 = 4
SLOW_FIGHT_FRAME2 = 12
STOP_TARGET_DIST_FACTOR = 3.
NFRAMES_DIRECTIONS = 16

DFIGHT = 3

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
        self.pos = self.rect.center
        self.direction = direction
        self.vel = self.unit.max_dist * ANIM_VEL
        self.target = None
        self.target_slot = None
        self.opponents = None
        self.friends = None
        self.targeted_by = []
        self.free_slots = {direction:True for direction in DELTAS}
        self.time_frome_last_direction_change = 1000
        #
        self.frame0 = random.randint(0,12)
        self.nframes = None
        self.isprite = None
        self.z = self.z
        self.direction = "left"
        self.refresh_sprite_type()
        self.dead = False
        self.dead_img = pygame.Surface(self.rect.size)
        self.dead_img.fill((255,0,0))


    def ask_slot(self):
        for direction in self.free_slots:
            if self.free_slots[direction]:
                return direction

    def get_target_slot_pos(self): #TODO: dx*s could be precomputed when target_slot is set
        dx,dy = self.target_slot
        s = self.battle.cell_size
        return self.target.pos[0]+dx*s//2, self.target.pos[1]+dy*s//2

    def update_target(self):
        nearest = self.get_nearest_free_ennemy()
        if nearest:
            self.set_target(nearest)

    def set_target(self, other):
        self.target = other
        self.target_slot = other.ask_slot()
        if self.target_slot:
            other.free_slots[self.target_slot] = False
        other.targeted_by.append(self)
        #reciprocity
        if not other.target:
            other.target = self
            other.target_slot = (-self.target_slot[0], -self.target_slot[1])


    def get_nearest_free_ennemy(self):
        x,y = self.pos
        distances = []
        best_d, best_o = float("inf"), None
        dok = STOP_TARGET_DIST_FACTOR*self.battle.cell_size
        for u in self.opponents:
            if len(u.targeted_by) < 4:
##            if not u.target:
                d = abs(x-u.pos[0]) + abs(y-u.pos[1])
                if d < dok:
                    return u
                elif d < best_d:
                    best_d, best_o = d, u
        return best_o

    def get_nearest_ennemy(self):
        x,y = self.pos
        distances = []
        best_d, best_o = float("inf"), None
        dok = STOP_TARGET_DIST_FACTOR*self.battle.cell_size
        for u in self.opponents:
            d = abs(x-u.pos[0]) + abs(y-u.pos[1])
            if d < dok:
                return u
            elif d < best_d:
                best_d, best_o = d, u
        return best_o

    def die(self):
        self.dead = True
        #tell goodbye to friends
        self.friends.remove(self)
        #tell the target that the slot is now free
        if self.target:
            self.target.free_slots[self.target_slot] = True
        #tell the ennemies to find someone else among friends
        for u in self.targeted_by:
            u.target = None
            u.target_slot = None
        #add himself to the list of deads
        self.battle.deads.append(self)



    def refresh_sprite_type(self):
        i,n,t = self.unit.sprites_ref[self.direction]
        self.isprite = i
        self.nframes = n
        # self.set_frame_refresh_type(t)


    # def choose_direction(self, dx, dy):
    #     if dx and dy:
    #         if random.random() < 0.5:
    #             self.direction = DELTA_TO_KEY[(dx,0)]
    #         else:
    #             self.direction = DELTA_TO_KEY[(0,dy)]
    #         if self.unit.team == 1:
    #             print(self.direction)
    #     else:
    #         if dx:
    #             self.direction = DELTA_TO_KEY[(dx,0)]
    #         elif dy:
    #             self.direction = DELTA_TO_KEY[(0,dy)]
    #         else:
    #             self.direction = DELTA_TO_KEY[(0,0)]

##    def choose_direction(self, dx, dy):
##        if dx:
##            self.direction = DELTA_TO_KEY[(dx,0)]
##        elif dy:
##            self.direction = DELTA_TO_KEY[(0,dy)]
##        else:
##            self.direction = DELTA_TO_KEY[(0,0)]

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


    def draw_and_move(self, surface):
        if self.dead:
            return
        #
        if self.target_slot:
            x,y = self.get_target_slot_pos()
        else:
            x,y = random.randint(0,self.battle.W), random.randint(0,self.battle.H)
            self.update_target()
        rdx = x - self.pos[0]
        rdy = y - self.pos[1]
        ########################################################################
        if self.target and abs(rdx) < DFIGHT and abs(rdy) < DFIGHT: #fighting
            self.direction = DELTA_TO_KEY_SLOT[self.target_slot]
            self.refresh_sprite_type()
            frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
            if not self.target.dead and not self.dead:
                result = self.unit.get_fight_result(self.target)
                if result < 0:
                    self.die()
                elif result > 0:
                    self.target.die()
        else: #walking
            self.refresh_dxdy(rdx, rdy)
            if self.time_frome_last_direction_change > NFRAMES_DIRECTIONS:
                self.direction = DELTA_TO_KEY[self.dxdy]
                self.refresh_sprite_type()
                self.time_frome_last_direction_change = 0
            frame = (self.frame0 + self.battle.fight_frame_walk)%self.nframes
            self.pos = (self.pos[0]+self.vel*self.dxdy[0],
                        self.pos[1]+self.vel*self.dxdy[1])
            self.rect.center = self.pos
##        if self.unit.team == 1:
##            print(self.direction, self.isprite, self.nframes, frame, frame+self.isprite)
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        surface.blit(img, self.rect)
        self.time_frome_last_direction_change += 1





#remettre un choose_direction aleatoire, mais forcer de pas changer tout les + que x frames
#accelerer batailles avec space (reduit les SLOWNESS), finir battaile avec enter (supprime fps et affichage)
#changer target pour cellule libre toujours, sinon autre target sinon attente.
#coller sang sur la map plutot que de continuer de bliter sang a chaque frame
#pas dans la neige et dans le sable
#cas ou terrain pas le meme dans deux units ? terrain = terrain de l'attaquant ou du defenseur ? ou plutot faire vite une map mixte ?
class Battle:

    def __init__(self, u1, u2, terrain, zoom_level):
        self.game = u1.game
        self.surface = thorpy.get_screen()
        self.W = self.surface.get_width()
        self.H = self.surface.get_height()
        self.u1 = u1
        self.u2 = u2
        self.terrain = terrain
        self.z = zoom_level
        self.cell_size = None
        self.f1 = []
        self.f2 = []
        self.f = []
        self.deads = []
        self.fights = []
        self.fight_t = 0
        self.fight_frame_walk = 0
        self.fight_frame_attack = 0

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
        self.surface.fill((255,255,255))
        for u in self.deads:
            self.surface.blit(u.dead_img, u.rect)
        for u in self.f:
            u.draw_and_move(self.surface)
        self.fight_t += 1
        if self.fight_t % SLOW_FIGHT_FRAME1 == 0:
            self.fight_frame_walk += 1
        if self.fight_t % SLOW_FIGHT_FRAME2 == 0:
            self.fight_frame_attack += 1
        pygame.display.flip()
        #
        self.f.sort(key=lambda x:x.pos[1]) #peut etre pas besoin selon systeme de cible
        if len(self.f1) == 0 or len(self.f2) == 0:
            thorpy.functions.quit_menu_func()


    def prepare_battle(self):
        screen = thorpy.get_screen()
        W,H = screen.get_size()
        s = self.u1.editor.zoom_cell_sizes[self.z]
        self.cell_size = s
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


    def update_targets(self):
        for u1 in self.f1:
            if not u1.target_slot:
                u1.update_target()
        for u2 in self.f2:
            if not u2.target_slot:
                u2.update_target()

