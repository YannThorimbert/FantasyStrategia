import os, random, thorpy

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
        #
        self.sounds = thorpy.SoundCollection()
        self.deny_sound = self.sounds.add("sounds/ui/deny.wav")[0]
        self.death_sounds = get_sounds("sounds/death/", self.sounds)
        self.hit_sounds = get_sounds("sounds/hits/", self.sounds)
        self.walk_sounds = get_sounds("sounds/footsteps/", self.sounds)
        self.outdoor_sound = self.sounds.add("sounds/atmosphere/nature.wav")[0]
        self.magic_attack_sounds = get_sounds("sounds/attacks/", self.sounds)
        for s in self.death_sounds:
            s.set_volume(0.5)
        self.is_flaggable = ["grass", "rock", "sand", "snow", "thin snow"]
        self.is_burnable = ["grass", "wood", "oak", "fir1", "fir2", "firsnow",
                            "palm", "bush", "village", "flag"]
        self.burning = {} #e.g. burning[(4,12):2] means 2 remaining turns to burn
        self.fire = InteractiveObject("fire", self.me, "sprites/fire")
##        self.fire.always_drawn_last = True



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

    def get_cell_at(self, x, y):
        return self.me.lm.get_cell_at(x,y)

    def get_unit_at(self, x, y):
        cell = self.get_cell_at(x,y)
        if cell:
            return cell.unit

    def remove_object(self, o):
        o.remove_from_map(self.me)

    def remove_unit(self, u): #just a wrapper
        u.remove_from_game()

    def set_fire(self, coord, n):
        #1. remove old fire if necessary
        if coord in self.burning:
            self.burning.pop(coord)
            for o in self.get_cell_at(coord[0],coord[1]).objects:
                if o.name == "fire":
                    fire = o
            self.remove_object(o)
        #2. add new fire
        if n > 0:
            cell = self.get_cell_at(coord[0],coord[1])
            self.burning[coord] = n
            self.add_obj_before_other_if_needed(self.fire,1,"village",cell)

    def add_obj_before_other_if_needed(self, obj, qty, other_name, cell):
        has_other = False
        for o in cell.objects:
            if o.name == other_name:
                has_other = True
                obj.min_relpos = [0, o.relpos[1]+0.001]
                obj.max_relpos = [0, o.relpos[1]+0.001]
                break
        self.add_object(cell.coord, obj, qty, has_other)

    def get_interactive_objects(self, x, y):
        return [o for o in self.get_cell_at(x,y).objects if o.can_interact]




##def add_game_gui_elements()