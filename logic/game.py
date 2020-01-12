import os, random, thorpy



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
        self.objects = []
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



    def add_unit(self, coord, unit, quantity):
        u = self.me.add_unit(coord, unit, quantity)
        u.team = u.race.team
        u.game = self
        self.units.append(u)

    def add_object(self, coord, obj, quantity):
        o = self.me.add_dynamic_object(coord, obj, quantity)
        o.game = self
        self.objects.append(o)

    def get_cell_at(self, x, y):
        return self.me.lm.get_cell_at(x,y)

    def get_unit_at(self, x, y):
        cell = self.get_cell_at(x,y)
        if cell:
            return cell.unit

    def add_fire(self, x, y):
        self.add_object((x,y), self.fire, 1)

    def get_interactive_objects(self, x, y):
        return [o for o in self.get_cell_at(x,y).objects if o.can_interact]
