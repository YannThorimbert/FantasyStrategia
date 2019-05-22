from PyWorld2D.mapobjects.objects import MapObject


DELTAS = ((1,0),(-1,0),(0,1),(0,-1))

class Unit(MapObject):

    def __init__(self, type_name, editor, fns, name="", factor=1., relpos=(0,0),
                    build=True, new_type=True):
        MapObject.__init__(self, editor, fns, name, factor, relpos, build, new_type)
        self.type_name = type_name
        self.cost = None
        self.max_dist = None
        self.race = None

    def _spawn_possible_destinations(self, x, y, tot_cost, path_to_here, score):
        for dx,dy in DELTAS:
            cx, cy = x+dx, y+dy #next cell
            next_cell = self.editor.lm.get_cell_at(cx,cy)
            if next_cell:
                no_key_value = float("inf"), None
                best_score, best_path = score.get((cx,cy), no_key_value)
                #compute the cost of the current path ##########################
                for obj in next_cell.objects:
                    if not isinstance(obj, Unit):
                        this_tot_cost = self.cost[obj.name]
                        break
                else: #if break is never reached
                    this_tot_cost = self.cost[next_cell.material.name]
                this_tot_cost += tot_cost #+ cost so far
                ################################################################
                if this_tot_cost <= self.max_dist: #should update the best
                    if this_tot_cost < best_score:
                        new_best_path = path_to_here + [(cx,cy)]
                        score[(cx,cy)] = this_tot_cost, new_best_path
                        self._spawn_possible_destinations(cx, cy, this_tot_cost,
                                                          new_best_path, score)

    def get_possible_destinations(self):
        score = {}
        x,y = self.cell.coord
        self._spawn_possible_destinations(x, y, 0., [self.cell.coord], score)
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
        #
        obj.cost = self.cost.copy()
        obj.max_dist = self.max_dist
        obj.race = self.race
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
        #
        obj.cost = self.cost.copy()
        obj.max_dist = self.max_dist
        obj.race = self.race
        return obj
