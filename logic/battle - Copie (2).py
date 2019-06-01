import random, thorpy
import pygame

##from .unit import DELTA_TO_KEY, DELTA_TO_KEY_A, KEY_TO_DELTA, DELTAS

DELTAS = ((1,0),(-1,0),(0,1),(0,-1))
DELTA_TO_KEY = {(0,0):"idle", (1,0):"right", (-1,0):"left", (0,1):"down", (0,-1):"up"}
KEY_TO_DELTA = {DELTA_TO_KEY[key]:key for key in DELTA_TO_KEY}
DELTA_TO_KEY_A = {(0,0):"idle", (1,0):"rattack", (-1,0):"lattack", (0,1):"down", (0,-1):"up"}
DELTA_TO_KEY_SLOT = {(-dx,-dy):DELTA_TO_KEY_A[(dx,dy)] for dx,dy in DELTA_TO_KEY_A}

ANIM_VEL = 0.5
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
        self.fighting_right_now = False
        self.in_pause = False
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
        self.dead_img.set_alpha(100)


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

    #probleme : other.target != self, alors que other.target in self.targeted_by

    def set_target(self, other):
##        assert self.target is None and self.target_slot is None
        if self.target:
            return
        free_slot = other.ask_slot()
        if free_slot:
            self.target_slot = free_slot
            other.free_slots[free_slot] = False
            self.target = other
            other.targeted_by.append(self)
            #reciprocity
            if self.target.target is None:
                this_slot = self.ask_slot()
                if this_slot:
                    other.target = self
                    other.target_slot = this_slot
                    self.targeted_by.append(other)
                    self.free_slots[this_slot] = False

    def unset_target(self):
        self.target.free_slots[self.target_slot] = True
        self.target = None
        self.target_slot = None

    def force_reciprocal(self):
        if self.target.target:
            self.target.unset_target()
        self.target.set_target(self)
        self.pos = self.get_target_slot_pos()
        self.rect.center = self.pos


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
            self.unset_target()
        #tell the ennemies to find someone else among friends
        for i in range(len(self.targeted_by)-1,-1,-1):
            u = self.targeted_by[i]
            if u.target is self:
                u.unset_target()
            self.targeted_by.pop()
        #add himself to the list of deads
        for u in self.opponents:
            if u.target is self:
                assert False


    def refresh_sprite_type(self):
        i,n,t = self.unit.sprites_ref[self.direction]
        self.isprite = i
        self.nframes = n

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
        x,y = self.pos
        if self.pos[0] > self.battle.W:
            x = self.battle.W
        elif self.pos[0] < 0:
            x = 0
        if self.pos[1] > self.battle.H:
            y = self.battle.H
        elif self.pos[1] < 0:
            y = 0
        self.pos = (x,y)


    def draw_and_move(self, surface):
        if self.dead:
            return
        #
##        if random.random() < 0.2:
##            self.in_pause = not(self.in_pause)
        if self.target_slot:
            x,y = self.get_target_slot_pos()
        else:
            x,y = random.randint(0,self.battle.W), random.randint(0,self.battle.H)
            self.update_target()
        rdx = x - self.pos[0]
        rdy = y - self.pos[1]
        ########################################################################
        self.fighting_right_now = False
        if self.target:
            near_target = self.target and abs(rdx) < DFIGHT and abs(rdy) < DFIGHT
            rec_fight = (self.target.target is self) and self.target.fighting_right_now
            if near_target or rec_fight: #fighting
                self.fighting_right_now = True
                if not self.target.fighting_right_now:
                    if not(self.target.target is self):
                        self.force_reciprocal()
                self.direction = DELTA_TO_KEY_SLOT[self.target_slot]
                self.refresh_sprite_type()
                frame = (self.frame0 + self.battle.fight_frame_attack)%self.nframes
                if not self.target.dead and not self.dead:
                    result = self.unit.get_fight_result(self.target)
                    if result < 0:
                        self.battle.to_remove.append(self)
                    elif result > 0:
                        self.battle.to_remove.append(self.target)
        if not self.fighting_right_now: #walking
            if not self.in_pause:
                self.fighting_right_now = False
                self.refresh_dxdy(rdx, rdy)
                if self.time_frome_last_direction_change > NFRAMES_DIRECTIONS:
                    self.direction = DELTA_TO_KEY[self.dxdy]
                    self.refresh_sprite_type()
                    self.time_frome_last_direction_change = 0
                frame = (self.frame0 + self.battle.fight_frame_walk)%self.nframes
                self.pos = (self.pos[0]+self.vel*self.dxdy[0],
                            self.pos[1]+self.vel*self.dxdy[1])
                self.stay_in_screen()
                self.rect.center = self.pos
            else:
                frame = 0
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
        self.correct_targets()
        self._check_health()
##        if self.fight_t % 100 == 0:
##            print("REINIT")
##            self.reinitialize_targets()
        self.update_targets()
        self.surface.fill((255,255,255))
        for u in self.deads:
            self.surface.blit(u.dead_img, u.rect)
            for u2 in u.opponents:
                if u2.target is u:
                    assert False
        for u in self.f:
            u.draw_and_move(self.surface)
        for u in self.to_remove:
            if not u.dead: #a single battle can add a unit twice in to_remove
                u.die()
                self.f.remove(u)
                self.deads.append(u)
        self.to_remove = []
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


    def update_targets(self):
        for u1 in self.f1:
            if not u1.target_slot:
                u1.update_target()
        for u2 in self.f2:
            if not u2.target_slot:
                u2.update_target()

    def reinitialize_targets(self):
        for u1 in self.f1:
            if u1.target:
                u1.unset_target()
                u1.update_target()
        for u2 in self.f2:
            if not u2.target_slot:
                u2.update_target()

    def correct_targets(self):
        for u1 in self.f:
            for u2 in u1.targeted_by:
                if not(u2.target is u1):
                    print("PROBLEME", u2.target, u1)
                    u2.target = u1
##                    u2.set_target(u1)

    def _check_health(self):
        for u1 in self.f:
            assert not u1 in self.deads
            assert not u1.dead
            for u2 in u1.targeted_by:
                assert not u2 in self.deads
                assert not u2.dead
                assert u2 in u1.opponents
##                assert u2.target is u1
        for d in self.deads:
            assert not d in self.f
            assert not d in d.friends
