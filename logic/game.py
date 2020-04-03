import os, random, pygame, thorpy
from FantasyStrategia.effects import effects
from FantasyStrategia.logic.unit import InteractiveObject

INCOME_PER_VILLAGE = 100

def sgn(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    return 0

def get_sprite_frames(fn, deltas=None, s=32, ckey=(255,255,255),
                        resize_factor=None):
    imgs = []
    sprites = pygame.image.load(fn)
    n = sprites.get_width() // s
    h = sprites.get_height()
    if resize_factor:
        s = int(resize_factor*s)
        w,h = sprites.get_size()
        w = int(resize_factor*w)
        h = int(resize_factor*h)
        sprites = pygame.transform.scale(sprites, (w,h))
    if not deltas:
        deltas = [(0,0) for i in range(n)]
    x = 0
    for i in range(n):
        surf = pygame.Surface((s,h))
        surf.fill(ckey)
        surf.set_colorkey(ckey)
        dx, dy = deltas[i]
        surf.blit(sprites, (dx,dy), pygame.Rect(x,0,s,h))
        imgs.append(surf)
        x += s
    return imgs


def get_sounds(root, sc, volume=None):
    sounds = []
    for fn in os.listdir(root):
        if fn.endswith(".wav") or fn.endswith(".mp3"):
            sound, fake = sc.add(os.path.join(root,fn))
            if not fake:
                if volume is not None:
                    sound.set_volume(volume)
                sounds.append(sound)
    return sounds



class Game:

    def __init__(self, me):
        self.me = me
        me.game = self
        self.gui = None
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
        self.coin_sound = self.sounds.add("sounds/ui/coin2.wav")[0]
        self.flag_sound = self.sounds.add("sounds/hits/new_hits_5.wav")[0]
        self.start_battle_sound = self.sounds.add("sounds/start_battle.wav")[0]
        self.fire_extinguish_sound = self.sounds.add("sounds/psht.wav")[0]
        self.fire_sound = self.sounds.add("sounds/fire.wav")[0]
        self.deny_sound = self.sounds.add("sounds/ui/deny2.wav")[0]
        self.death_sounds = get_sounds("sounds/death/", self.sounds)
        self.hit_sounds = get_sounds("sounds/hits/", self.sounds)
        self.walk_sounds = get_sounds("sounds/footsteps/", self.sounds)
        self.outdoor_sound = self.sounds.add("sounds/atmosphere/nature.wav")[0]
        self.magic_attack_sounds = get_sounds("sounds/magic/attacks/", self.sounds)
        self.magic_explosion_sounds = get_sounds("sounds/magic/explosions/", self.sounds)
        for s in self.death_sounds:
            s.set_volume(0.5)
        self.is_flaggable = ["grass", "rock", "sand", "snow", "thin snow"]
        self.is_burnable = ["grass", "bridge_v", "bridge_h", "oak", "fir1",
                            "fir2", "firsnow", "palm", "bush", "village",
                            "flag", "forest", "flag"]
        self.burning = {} #e.g. burning[(4,12):2] means 2 remaining turns to burn
        self.fire = InteractiveObject("fire", self.me, "sprites/fire")
        self.fire.min_relpos=[0,-0.4]
        self.fire_max_relpos=[0,-0.4]
        self.fire.relpos=[0,-0.4]
        self.bridge_v, self.bridge_h = None, None
        self.bridges = []
        #
        self.smokes_log = {}
        effects.initialize_smokegens()
##        self.fire.always_drawn_last = True
        #

    def set_ambiant_sounds(self, val):
        if val:
            self.outdoor_sound.play(-1)
            if self.burning:
                self.fire_sound.play(-1)
        else:
            self.outdoor_sound.stop()
            if self.burning:
                self.fire_sound.stop()


    def add_smoke(self, type_, coord, delta=None, what=""):
        if type_ == "small":
            sg = effects.smokegen_small
        else:
            sg = effects.smokegen_large
        smoke = effects.GameSmoke(self.me.cam, sg, coord, delta)
        self.smokes_log[coord] = smoke

    def remove_smoke(self, coord):
        return self.smokes_log.pop(coord, None)

    def refresh_smokes(self):
        effects.refresh_smokes(self)

    def recompute_smokes_position(self):
        for s in self.smokes_log.values():
            s.refresh_pos()

    def extinguish(self, coord, natural_end=False):
        self.remove_fire(coord)
        if not self.burning:
            self.fire_sound.stop()
        if natural_end: #then the burnable objects are removed
            objs = self.get_cell_at(coord[0],coord[1]).objects
            to_burn = [o for o in objs if o.str_type in self.is_burnable]
            for o in to_burn:
                self.fire_extinguish_sound.play_next_channel()
                o.remove_from_map(self.me)
                effects.draw_ashes(self, o)

    def set_players(self, players, current=0):
        self.players = players
        self.current_player = self.players[current]
        self.current_player_i = current

    def get_players_from_team(self, team):
        return [p for p in self.players if p.team == team]

    def update_fire_logic(self):
        to_extinguish = []
        for coord in self.burning:
            for obj in self.get_cell_at(coord[0],coord[1]).objects:
                if obj.name == "fire":
                    self.burning[coord] -= 1
                    if self.burning[coord] == 0:
                        to_extinguish.append(coord)
                    elif self.burning[coord] == 2:
                        self.add_smoke("small", coord, (0,-0.3), "fire")
                    elif self.burning[coord] == 1:
                        self.remove_smoke(coord)
                        self.add_smoke("large", coord, (0,-0.3), "fire")
        for coord in to_extinguish:
            self.extinguish(coord, natural_end=True)

    def refresh_village_gui(self):
        nvillages = self.count_villages(self.current_player.team)
        self.gui.e_pop_txt.set_text(str(nvillages))

    def end_turn(self):
        self.need_refresh_ui_box = True
        self.update_fire_logic()
        self.current_player_i += 1
        self.current_player_i %= len(self.players)
        self.current_player = self.players[self.current_player_i]
        self.refresh_village_gui()
        for u in self.units:
            u.is_grayed = False
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
        self.gui.has_moved = []
        #
        from_ = self.current_player.money
        self.update_player_income(self.current_player)
        self.gui.show_animation_income(from_, self.current_player.money)
        self.gui.e_gold_txt.set_text(str(self.current_player.money))

    def func_reac_time(self):
        self.gui.refresh()
        self.me.func_reac_time()
        self.t += 1
        pygame.display.flip()


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
        return u

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


##    def remove_unit(self, u): #just a wrapper
##        u.remove_from_game()

    def set_flag(self, coord, flag_template, team, sound=False):
        if sound:
            self.flag_sound.play()
        cell = self.get_cell_at(coord[0],coord[1])
##        o = self.add_obj_before_other_if_needed(flag_template,
##                                                 1, ["village"], cell)
        o = self.add_object(cell.coord, flag_template, 1, True)
        o.team = team

    def remove_fire(self, coord):
        if coord in self.burning:
            self.burning.pop(coord)
            for o in self.get_cell_at(coord[0],coord[1]).objects:
                if o.str_type == "fire":
                    o.remove_from_map(self.me)
        self.remove_smoke(coord)


    def set_fire(self, coord, n):
        #1. remove old fire if necessary
        self.remove_fire(coord)
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
        return o


    def get_interactive_objects(self, x, y):
        return [o for o in self.get_cell_at(x,y).objects if o.can_interact]

    def get_all_objects_by_name(self, name):
        objs = []
        for x in range(self.me.lm.nx):
            for y in range(self.me.lm.ny):
                cell = self.get_cell_at(x,y)
                for o in cell.objects:
                    if o.name == name:
                        objs.append(o)
        return objs

    def get_all_objects_by_str_type(self, str_type):
        objs = []
        for x in range(self.me.lm.nx):
            for y in range(self.me.lm.ny):
                cell = self.get_cell_at(x,y)
                for o in cell.objects:
                    if o.str_type == str_type:
                        objs.append(o)
        return objs

    def get_map_size(self):
        return self.me.lm.nx, self.me.lm.ny

    def count_villages(self, team):
        counter = 0
        for f in self.get_all_objects_by_str_type("flag"):
            if f.team == team:
                for o in f.cell.objects:
                    if o.name == "village":
                        counter += 1
                        break
        return counter


##    def update_players_income(self):
##        for p in self.players:
##            v = self.count_villages(p.team)
##            INCOME_PER_VILLAGE = 100
##            tax_per_village = 1. #for the moment
##            p.money += v*INCOME_PER_VILLAGE * tax_per_village
####            update_gui_villages_money(v, p.money)


    def update_player_income(self, p):
        v = self.count_villages(p.team)
        tax_per_village = 1. #for the moment
        p.money += int(v*INCOME_PER_VILLAGE * tax_per_village)


    def get_units_of_player(self, p):
        for u in self.units:
            if u.team == p.team:
                yield u

    def get_race_of_player(self, p):
        for u in self.get_units_of_player(p):
            return u.race





##def add_game_gui_elements()
