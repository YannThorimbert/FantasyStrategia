import random, thorpy
import pygame

##from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}



ANIM_VEL = 0.2
SLOW_FIGHT_FRAME1 = 4
SLOW_FIGHT_FRAME2 = 16
STOP_TARGET_DIST_FACTOR = 3.

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
        #
        self.frame0 = random.randint(0,12)
        self.nframes = None
        self.isprite = None
        self.z = self.z
        self.set_sprite_type("left")
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

    def set_target(self, other):
        self.target = other
        self.target_slot = other.ask_slot()
        if self.target_slot:
            other.free_slots[self.target_slot] = False
        other.targeted_by.append(self)


    def get_nearest_free_ennemy(self):
        x,y = self.pos
        distances = []
        best_d, best_o = float("inf"), None
        dok = STOP_TARGET_DIST_FACTOR*self.battle.cell_size
        for u in self.opponents:
            if not u.target:
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
        self.target.free_slots[self.target_slot] = True
        #tell the ennemies to find someone else among friends
        for u in self.targeted_by:
            u.target = None
            u.target_slot = None
        #add himself to the list of deads
        self.battle.deads.append(self)



    def set_sprite_type(self, key):
        i,n,t = self.unit.sprites_ref[key]
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

    def choose_direction(self, rdx, rdy):
        adx = abs(rdx)
        ady = abs(rdy)
        if adx > ady:
            if rdx > 0:
                return 1,0
            else:
                return -1,0
        else: #must not stay at rest
            if rdy > 0:
                return 0, 1
            else:
                return 0, -1


    def choose_direction_attack(self, dx, dy):
        if dx:
            self.direction = DELTA_TO_KEY[(dx,0)]
        elif dy:
            self.direction = DELTA_TO_KEY[(0,dy)]

##    def set_compatible_slot(self):
##        if self.target.target is self:
##            dx = self.target.pos[0] - self.pos[0]
##            dy = self.target.pos[1] - self.pos[1]
##            if dx > 0: #ennemy is on the right
##                if dy > 0: #ennemy is on the top
##                    if dx > dy: #more on the right than on the top
##                        self_slot = (1,0)
##                        target_slot = (-1,0)
##                    else: #more on the top than on the right
##                        self_slot = (0,-1)
##                        target_slot = (0,1)
##                else: #ennemy is on the bottom
##                    if dx > dy: #more on the right than on the bottom
##                        self_slot = (1,0)
##                        target_slot = (-1,0)
##                    else: #more on the bottom than on the right
##                        self_slot = (0,1)
##                        target_slot = (0,-1)
##            else: #ennemy is on the left
##                if dy > 0: #ennemy is on the top
##                    if dx > dy: #more on the left than on the top
##                        self_slot = (-1,0)
##                        target_slot = (1,0)
##                    else: #more on the top than on the left
##                        self_slot = (0,-1)
##                        target_slot = (0,1)
##                else: #ennemy is on the bottom
##                    if dx > dy: #more on the left than on the bottom
##                        self_slot = (-1,0)
##                        target_slot = (1,0)
##                    else: #more on the bottom than on the left
##                        self_slot = (0,1)
##                        target_slot = (0,-1)
##            ####################################################################
##            self.target_slot = self_slot
##            self.target.target_slot = target_slot
##            for u in self.target.targeted_by:
##                if u is not self:
##                    u.target_slot = None
##            for u in self.targeted_by:
##                if u is not self.target:
##                    u.target_slot = None


    def set_compatible_slot(self): il y a un bug car le vert sarrete bcp trop tot
        self.vel = 0.
##        self.target.pos = self.target.get_target_slot_pos()
##        self.pos = self.get_target_slot_pos()




    def draw_and_move(self, surface):
        if self.dead:
            return
        #
        if self.target_slot:
            x,y = self.get_target_slot_pos()
        else:
            x,y = random.randint(0,self.battle.W), random.randint(0,self.battle.H)
        rdx = x - self.pos[0]
        rdy = y - self.pos[1]
        ########################################################################
        if self.target:
            if abs(rdx) < 40 and abs(rdy) < 40:
                if self.target.target is self:
                    self.set_compatible_slot()
                frame = (self.frame0 + self.battle.fight_frame2)%self.nframes
                result = self.unit.get_fight_result(self.target)
                if result < 0:
                    self.die()
                elif result > 0:
                    self.target.die()
                dx = sgn(rdx)
                dy = sgn(rdy)
                self.choose_direction_attack(dx,dy)
                self.set_sprite_type(self.direction)
            else:
                frame = (self.frame0 + self.battle.fight_frame1)%self.nframes
                dx,dy = self.choose_direction(rdx, rdy)
                self.direction = DELTA_TO_KEY[(dx,dy)]
                if self.unit.team == 1:
                    print(rdx, rdy, "--->", dx, dy, self.direction)
##                dx, dy =  KEY_TO_DELTA[self.direction] #if you remove this, units can move in diagonal
                self.set_sprite_type(self.direction)
                #
                self.pos = (self.pos[0]+self.vel*dx, self.pos[1]+self.vel*dy)
                self.rect.center = self.pos
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        surface.blit(img, self.rect)





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
        self.fight_frame1 = 0
        self.fight_frame2 = 0
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
            self.fight_frame1 += 1
        if self.fight_t % SLOW_FIGHT_FRAME2 == 0:
            self.fight_frame2 += 1
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
        initialize_targets(self.f1, self.f2)
        self.f = self.f1 + self.f2


    def update_targets(self):
        for u1 in self.f1:
            if not u1.target_slot:
                nearest = u1.get_nearest_free_ennemy()
                u1.set_target(nearest)
        for u2 in self.f2:
            if not u2.target_slot:
                nearest = u2.get_nearest_free_ennemy()
                u2.set_target(nearest)


def initialize_targets(f1, f2):
    for u1 in f1:
        nearest_free = u1.get_nearest_free_ennemy()
        if nearest_free:
            u1.set_target(nearest_free)
            nearest_free.set_target(u1)
    for u1 in f1:
        if not u1.target:
            nearest = u1.get_nearest_ennemy()
            u1.set_target(nearest)
    for u2 in f2:
        if not u2.target:
            nearest = u2.get_nearest_ennemy()
            u2.set_target(nearest)
