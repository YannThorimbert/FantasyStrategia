from PyWorld2D.mapobjects.objects import MapObject


std_cost_material = {'Deep water': float("inf"),
                     'Grass': 1,
                     'Rock': 2,
                     'Sand': 2,
                     'Shallow water': float("inf"),
                     'Snow': 4,
                     'Thin snow': 3,
                     'Water': float("inf"),
                     'outside': float("inf")}

#these are used as multipliers on the base material of the cell
std_cost_objects = {'forest': 1.5,
                    'cobblestone':0.5,
                    'village':0.5,
                    'wood':0.5,
                    'river':3,
                    'bush':1.5}

class Unit(MapObject):

    def __init__(self, type_name, editor, fns, name="", factor=1., relpos=(0,0),
                    build=True, new_type=True):
        MapObject.__init__(self, editor, fns, name, factor, relpos, build, new_type)
        self.type_name = type_name
        self.costs_material = std_cost_material.copy()
        self.costs_objects = std_cost_objects.copy()
        self.deltas = ((1,0),(-1,0),(0,1),(0,-1))
        self.max_dist = 3

    def _spawn_possible_destinations(self, x, y, tot_cost, score):
        for dx,dy in self.deltas:
            cx, cy = x+dx, y+dy
            cell = self.editor.lm.get_cell_at(cx,cy)
            if cell:
                best_score = score.get((cx,cy), float("inf"))
                cost_material = self.costs_material[cell.material.name]
                mult_object = 1.
                for obj in cell.objects:
                    if not isinstance(obj, Unit):
                        mult_object = self.costs_objects[obj.name]
                        break
                this_tot_cost = tot_cost + cost_material*mult_object
                if this_tot_cost <= self.max_dist:
                    if this_tot_cost < best_score:
                        score[(cx,cy)] = this_tot_cost
                        self._spawn_possible_destinations(cx, cy, this_tot_cost, score)

    def get_possible_destinations(self):
        score = {}
        x,y = self.cell.coord
        self._spawn_possible_destinations(x, y, 0., score)
        return score


    def copy(self):
        """The copy references the same images as the original !"""
        self.ncopies += 1
        obj = Unit(self.type_name, self.editor, [""], self.name, self.factor,
                        list(self.relpos), new_type=False)
        obj.original_imgs = self.original_imgs
        obj.nframes = self.nframes
        obj.imgs_z_t = self.imgs_z_t
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.object_type = self.object_type
        obj.quantity = self.quantity
        obj.fns = self.fns
        return obj

    def deep_copy(self):
        obj = Unit(self.type_name, self.editor, [""], self.name, self.factor,
                        list(self.relpos), new_type=False)
        obj.quantity = self.quantity
        obj.fns = self.fns
        obj.original_imgs = [i.copy() for i in self.original_imgs]
        obj.nframes = len(obj.original_imgs)
        obj.imgs_z_t = []
        for frame in range(len(self.imgs_z_t)):
            obj.imgs_z_t.append([])
            for scale in range(len(self.imgs_z_t[frame])):
                obj.imgs_z_t[frame].append(self.imgs_z_t[frame][scale].copy())
##        for imgs in self.imgs_z_t:
##            obj.imgs_z_t = [i.copy() for i in imgs]
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.object_type = self.object_type
        return obj
