import random, thorpy
import pygame

from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS



ANIM_VEL = 0.1
SLOW_FIGHT_FRAME1 = 4
SLOW_FIGHT_FRAME2 = 16
STOP_TARGET_DIST_FACTOR = 3.

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
        self.current_destination = None
        self.fighting = False
        self.opponents = None
        self.targeted_by = []
        #
        self.frame0 = random.randint(0,12)
        self.nframes = None
        self.isprite = None
        self.z = self.z
        self.set_sprite_type("left")
        self.dead = False
        self.dead_img = pygame.Surface(self.rect.size)
        self.dead_img.fill((255,0,0))

    def set_target(self, other):
        other.targeted_by.append(self)
        self.target = other
        self.refresh_current_destination()

    def unset_target(self):
        self.target.targeted_by.remove(self)
        self.target = None


    def set_sprite_type(self, key):
        i,n,t = self.unit.sprites_ref[key]
        self.isprite = i
        self.nframes = n
        # self.set_frame_refresh_type(t)

    def update_target(self):
        x,y = self.pos
        distances = []
        best_d, best_o = float("inf"), None
        for u in self.opponents:
            d = abs(x-u.pos[0]) + abs(y-u.pos[1])
            if d < STOP_TARGET_DIST_FACTOR*self.battle.cell_size:
                self.set_target(u)
                return
            else:
                if d < best_d:
                    best_d, best_o = d, u
        self.set_target(best_o)

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

    def choose_direction(self, dx, dy):
        if dx:
            self.direction = DELTA_TO_KEY[(dx,0)]
        elif dy:
            self.direction = DELTA_TO_KEY[(0,dy)]
        else:
            self.direction = DELTA_TO_KEY[(0,0)]


    def choose_direction_attack(self, dx, dy):
        if dx:
            self.direction = DELTA_TO_KEY[(dx,0)]
        elif dy:
            self.direction = DELTA_TO_KEY[(0,dy)]

    def refresh_current_destination(self):
        already_taken = []
        for u in self.target.targeted_by:
            if u is not self:
                if u.fighting:
                    already_taken.append(u.rect)
        if already_taken:
            print("PROBLEM")
            for dx,dy in DELTAS:
                r = self.target.rect.move(dx,dy)
                if not r.collidelist(already_taken):
                    self.current_destination = r.center
                    return
        self.current_destination = self.target.rect.move(3*self.battle.cell_size,0)

    def draw_and_move(self, surface):
        if self.dead:
            return
        if self.target.dead:
            self.unset_target()
            self.update_target()
        if self.fighting:
            frame = (self.frame0 + self.battle.fight_frame2)%self.nframes
        else:
            frame = (self.frame0 + self.battle.fight_frame1)%self.nframes
        frame += self.isprite
        img = self.unit.imgs_z_t[self.z][frame]
        surface.blit(img, self.rect)
        #
        if not self.fighting:
            rdx = self.target.pos[0] - self.pos[0]
            rdy = self.target.pos[1] - self.pos[1]
        else:
            rdx = self.current_destination[0] - self.pos[0]
            rdy = self.current_destination[1] - self.pos[1]
        #update direction ######################################################
        dx = sgn(rdx)
        dy = sgn(rdy)
        ########################################################################
        if abs(rdx) < 30 and abs(rdy) < 30:
            # print("ENTER")
            self.vel = 0.
            self.choose_direction_attack(dx,dy)
            if not self.fighting: #just entered the fight
                self.refresh_current_destination()
            self.fighting = True
            self.set_sprite_type(self.direction)
            if self.unit.team < self.target.unit.team: #prevent doublons
                self.battle.fights.append((self, self.target))
            return
        else:
            # print(self.battle.fight_frame1)
            self.vel = self.unit.max_dist * ANIM_VEL
            self.choose_direction(dx,dy)
            self.fighting = False
            dx, dy =  KEY_TO_DELTA[self.direction] #if you remove it, units can move in diagonal
            self.set_sprite_type(self.direction)
            #
            self.pos = (self.pos[0]+self.vel*dx, self.pos[1]+self.vel*dy)
            self.rect.center = self.pos





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
        to_remove, deads = self.game.update_fights(self.fights)
        self.deads += deads
        for i in to_remove[::-1]:
            self.fights.pop(i)
            if u in self.f1:
                self.f1.remove(u)
            elif u in self.f2:
                self.f2.remove(u)
        if len(self.f1) == 0 or len(self.f2) == 0:
            thorpy.functions.quit_menu_func()

    def update_all_targets(self): #trick : faire un break si distance < 2*s
        for u1 in self.f1:
            u1.update_target()
        for u2 in self.f2:
            u2.update_target()


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
        for u2 in self.f2:
            u2.opponents = self.f1
        self.update_all_targets()
        self.f = self.f1 + self.f2
