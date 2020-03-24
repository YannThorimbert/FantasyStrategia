import os, random, thorpy
from FantasyStrategia.effects.effects import draw_ashes
from .unit import InteractiveObject



def get_sounds(root, sc):
    sounds = []
    for fn in os.listdir(root):
        if fn.endswith(".wav") or fn.endswith(".mp3"):
            sound, fake = sc.add(os.path.join(root,fn))
            if not fake:
                sounds.append(sound)
    return sounds



class Game:

    def __init__(self, me):
        self.me = me
        self.units = []
        self.t = 0
        self.days_left = 10 #set -1 for an infinite number of days
        self.days_elapsed = 1
        self.current_player = None
        self.players = None
        self.current_player_i = None
        self.need_refresh_ui_box = True
        #
        self.sounds = thorpy.SoundCollection()
        self.fire_extinguish_sound = self.sounds.add("sounds/psht.wav")[0]
        self.fire_sound = self.sounds.add("sounds/feuxxx.wav")[0]
        self.deny_sound = self.sounds.add("sounds/ui/deny2.wav")[0]
        self.death_sounds = get_sounds("sounds/death/", self.sounds)
        self.hit_sounds = get_sounds("sounds/hits/", self.sounds)
        self.walk_sounds = get_sounds("sounds/footsteps/", self.sounds)
        self.outdoor_sound = self.sounds.add("sounds/atmosphere/nature.wav")[0]
        self.magic_attack_sounds = get_sounds("sounds/attacks/", self.sounds)
        for s in self.death_sounds:
            s.set_volume(0.5)
        self.is_flaggable = ["grass", "rock", "sand", "snow", "thin snow"]
        self.is_burnable = ["grass", "bridge_v", "bridge_h", "oak", "fir1",
                            "fir2", "firsnow", "palm", "bush", "village",
                            "flag", "forest"]
        self.burning = {} #e.g. burning[(4,12):2] means 2 remaining turns to burn
        self.fire = InteractiveObject("fire", self.me, "sprites/fire")
        self.fire.min_relpos=[0,-0.4]
        self.fire_max_relpos=[0,-0.4]
        self.fire.relpos=[0,-0.4]
        self.bridge_v, self.bridge_h = None, None
        self.bridges = []
##        self.fire.always_drawn_last = True

    def extinguish(self, coord, natural_end=False):
        if natural_end: #then the burnable objects are removed
            print("***Natural extinguish")
            for o in self.get_cell_at(coord[0],coord[1]).objects:
                if o.str_type in self.is_burnable:
                    self.fire_extinguish_sound.play()
                    o.remove_from_map(self.me)
                    draw_ashes(self.me, o)
                    thorpy.get_application().pause(unpause_after=1000)
##                if o.str_type in self.is_burnable:
##                    cs = self.me.lm.get_current_cell_size()
##                    rect, img = o.get_fakerect_and_img(cs)
##                    ashes = draw_ashes(self.me, o)
##                    o.remove_from_map(self.me)
##                    import pygame
##                    clock = pygame.time.Clock()
##                    self.fire_extinguish_sound.play()
##                    img = ashes[0][0]
##                    for i in range(255):
##                        img.set_alpha(i)
##                        self.me.draw()
##                        self.me.screen.blit(img,rect)
##                        pygame.display.update(rect)
##                    for img in ashes[0]:
##                        clock.tick(30)
##                        self.me.draw()
##                        self.me.screen.blit(img,rect)
##                        pygame.display.update(rect)
##                    thorpy.get_application().pause(unpause_after=1000)
        self.set_fire(coord, 0)
        if not self.burning:
            self.fire_sound.stop()


    def set_players(self, players, current=0):
        self.players = players
        self.current_player = self.players[current]
        self.current_player_i = current

    def get_players_from_team(self, team):
        return [p for p in self.players if p.team == team]

    def end_turn(self):
        self.need_refresh_ui_box = True
        to_extinguish = []
        for x,y in self.burning:
            for obj in self.get_cell_at(x,y).objects:
                if obj.name == "fire":
                    self.burning[(x,y)] -= 1
                    if self.burning[(x,y)] == 0:
                        to_extinguish.append((x,y))
        for coord in to_extinguish:
            self.extinguish(coord, natural_end=True)
        self.current_player_i += 1
        self.current_player_i %= len(self.players)
        self.current_player = self.players[self.current_player_i]
        if self.current_player_i == 0:
            self.days_elapsed += 1
            self.current_player_i = 0
            #process other things to reinitialize each turn:
            ...
            if self.days_left == 1:
                #end game
                ...
            elif self.days_left > 1:
                self.days_left -= 1


    def build_map(self, map_initializer, fast, use_beach_tiler, load_tilers):
        map_initializer.build_map(self.me, fast, use_beach_tiler, load_tilers)
        for obj in self.me.lm.static_objects:
            if obj.str_type == "bridge_h":
                if self.bridge_h is None:
                    self.bridge_h = InteractiveObject("bridge", self.me,
                                                (obj.original_imgs[0],"idle"),
                                                str_type="bridge_h")
                    self.bridge_h.burnable = True
                    self.bridge_h.is_ground = True
                self.add_object(obj.cell.coord, self.bridge_h, 1)
                self.bridges.append(obj.cell.coord)
            if obj.str_type == "bridge_v":
                if self.bridge_v is None:
                    self.bridge_v = InteractiveObject("bridge", self.me,
                                                (obj.original_imgs[0],"idle"),
                                                str_type="bridge_v")
                    self.bridge_v.burnable = True
                    self.bridge_v.is_ground = True
                self.add_object(obj.cell.coord, self.bridge_v, 1)
                self.bridges.append(obj.cell.coord)

    def add_unit(self, coord, unit, quantity):
        u = self.me.add_unit(coord, unit, quantity)
        u.team = u.race.team
        u.game = self
        self.units.append(u)

    def add_object(self, coord, obj, quantity, rand_relpos=False):
        o = self.me.add_dynamic_object(coord, obj, quantity)
        o.game = self
        if rand_relpos:
            o.randomize_relpos()
        return o

    def get_cell_at(self, x, y):
        return self.me.lm.get_cell_at(x,y)

    def get_unit_at(self, x, y):
        cell = self.get_cell_at(x,y)
        if cell:
            return cell.unit

    def remove_object(self, o):
        o.remove_from_map(self.me)

##    def remove_unit(self, u): #just a wrapper
##        u.remove_from_game()

    def set_fire(self, coord, n):
        #1. remove old fire if necessary
        if coord in self.burning:
            self.burning.pop(coord)
            for o in self.get_cell_at(coord[0],coord[1]).objects:
                if o.str_type == "fire":
                    fire = o
            self.remove_object(o)
        #2. add new fire
        if n > 0:
            self.fire_sound.play(-1)
            cell = self.get_cell_at(coord[0],coord[1])
            self.burning[coord] = n
            names = ("village","bridge","forest")
            self.add_obj_before_other_if_needed(self.fire,1,names,cell)

    def add_obj_before_other_if_needed(self, obj, qty, other_names, cell):
        has_other = False
        for o in cell.objects:
            for n in other_names:
                if o.name == n:
                    if o.relpos[1] >= obj.relpos[1]:
                        has_other = True
                        s = self.me.lm.get_current_cell_size()
                        im2, r2 = o.get_current_img_and_rect(s)
                        cell_rect = o.get_current_rect(s)
                        obj.cell = cell
                        obj_rect = obj.get_current_img().get_rect()
                        obj_rect.bottom = r2.bottom + 1
                        obj.cell = None
                        #pos = centercell + relpos*s
                        #<==> relpos = (pos - centercell)/s
                        relpos = (obj_rect.centery - cell_rect.centery) / s
                        obj.min_relpos = [0, relpos]
                        obj.max_relpos = [0, relpos]
                        break
        o = self.add_object(cell.coord, obj, qty, has_other)

    def get_interactive_objects(self, x, y):
        return [o for o in self.get_cell_at(x,y).objects if o.can_interact]

    def get_all_objects_by_name(self, name):
        objs = []
        for x in self.me.lm.nx:
            for y in self.me.lm.ny:
                cell = self.get_cell_at(x,y)
                for o in cell.objects:
                    if o.name == name:
                        objs.append(o)
        return o






##def add_game_gui_elements()
