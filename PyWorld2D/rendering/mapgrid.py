import math
import pygame
from thorpy.gamestools.basegrid import BaseGrid
from thorpy.gamestools.grid import PygameGrid
from PyWorld2D.rendering.tilers.tilemanager import get_couple
import PyWorld2D.constants as const

#pour eviter de tj faire des tuples, ne pas heriter de PygameGrid et faire moi meme
VON_NEUMAN = [(-1,0), (1,0), (0,-1), (0,1)]
WATER = 1
GRASS = 0

##from thorpy import Monitor
##monitor = Monitor()

SUBMAP_FACTOR = 200

class LogicalCell:

    def __init__(self, h, coord, logical_map):
        self.map = logical_map
        self.couple = get_couple(h, self.map.material_couples)
        self.h = h
        self.coord = coord
        if h > self.couple.transition:
            self.value = GRASS
            self.material = self.couple.grass
        else:
            self.value = WATER
            self.material = self.couple.water
        self.type = None
        self.name = ""
        self.objects = []
        self.unit = None
##        self.imgs = None

    def set_name(self,name):
        self.name = name
        self.map.me.modified_cells.append(self.coord)

    def get_neighbors_von_neuman(self):
        for dx,dy in VON_NEUMAN:
            yield self.map.get_cell_at(self.coord[0]+dx, self.coord[1]+dy)

    def get_altitude(self):
        return (self.h-0.6)*2e4

    def get_static_img_at_zoom(self, level):
        return self.map.get_static_img_at_zoom(self.coord, level)

    def has_object_name(self, name):
        for o in self.objects:
            if o.name == name:
                return True
        return False

    def distance_to(self, other):
        return abs(self.coord[0]-other.coord[0]) + abs(self.coord[1]-other.coord[1])

class WhiteLogicalCell:

    def __init__(self, logical_map):
        self.map = logical_map
        self.imgs = None

    def get_static_img_at_zoom(self, level):
        return self.map.get_static_img_at_zoom(self.coord, level)


class GraphicalCell:

    def __init__(self):
        self.imgs = None



class LogicalMap(BaseGrid):

    def __init__(self, hmap, material_couples, actual_frames, outsides,
                    restrict_size):
        self.material_couples = material_couples
        self.zoom_levels = list(range(len(material_couples[0].tilers)))
        self.current_zoom_level = 0
        self.actual_frames = actual_frames
        if restrict_size is None:
            nx, ny = len(hmap), len(hmap[0])
        else:
            nx, ny = restrict_size
        BaseGrid.__init__(self, int(nx), int(ny))
        self.current_x = 0
        self.current_y = 0
        self.graphical_maps = [] #list of maps, index = zoom level
        self.cell_sizes = []
        for z in self.zoom_levels:
            cell_size = material_couples[0].get_cell_size(z)
            gm = GraphicalMap(nx, ny, cell_size, z, actual_frames[z], outsides[z])
            self.graphical_maps.append(gm)
            self.cell_sizes.append(cell_size)
        self.current_gm = self.graphical_maps[0]
        #
        self.nframes = len(material_couples[0].get_tilers(0))
        self.t = 0 #in unit of materials frame
        self.t2 = 0 #used for fast animated graphics
        self.t3 = 0
        self.tot_time = 0 #in unit of pygame frame
        self.frame_slowness = 20 #associated to t1
        self.frame_slowness2 = 3 #associated to t2
        self.frame_slowness3 = 40
        #
        self.refresh_cell_heights(hmap)
        self.refresh_cell_types()
        self.colorkey = None #used at build_surface()
        self.static_objects = []
        self.me = None

    def get_slowness(self,number):
        if number == const.NORMAL:
            return self.frame_slowness
        elif number == const.FAST:
            return self.frame_slowness2
        elif number == const.SLOW:
            return self.frame_slowness3


    def get_current_cell_size(self):
        return self.cell_sizes[self.current_zoom_level]

    def set_zoom(self, level):
        self.current_zoom_level = level
        self.current_gm = self.graphical_maps[level]
        if self.current_x < 0:
            self.current_x = 0
        elif self.current_x > self.nx-2:
            self.current_x = self.nx-2
        if self.current_y < 0:
            self.current_y = 0
        elif self.current_y > self.ny-2:
            self.current_y = self.ny-2

    def next_frame(self):
        self.tot_time += 1
        if self.tot_time % self.frame_slowness2 == 0:
            self.t2 += 1
        if self.tot_time % self.frame_slowness3 == 0:
            self.t3 += 1
        if self.tot_time % self.frame_slowness == 0:
            self.t = (self.t+1) % self.nframes
            return True

    def refresh_cell_heights(self, hmap):
        for x,y in self:
            self[x,y] = LogicalCell(hmap[x][y], (x,y), self)


    def get_cell_at(self, x, y):
        if self.is_inside((x,y)):
            return self[x,y]
        else:
            return None

    def get_neighbour_value_at(self, x, y, x0, y0):
        neighbour = self.get_cell_at(x,y)
        origin = self[x0,y0]
        if neighbour is None:
            return origin.value #then returns the same as demanding
        else:
            if neighbour.material is origin.material:
                return origin.value
            elif neighbour.material.hmax > origin.material.hmax:
                return GRASS
            else:
                return WATER

    def refresh_cell_types(self):
        for x,y in self:
            cell = self[x,y]
            if cell.value == GRASS:
                t = self.get_neighbour_value_at(x,y-1,x,y)
                b = self.get_neighbour_value_at(x,y+1,x,y)
                l = self.get_neighbour_value_at(x-1,y,x,y)
                r = self.get_neighbour_value_at(x+1,y,x,y)
                n = t*"t" + b*"b" + l*"l" + r*"r"
                if not n:
                    n = "c"
                tl = self.get_neighbour_value_at(x-1,y-1,x,y)
                tr = self.get_neighbour_value_at(x+1,y-1,x,y)
                bl = self.get_neighbour_value_at(x-1,y+1,x,y)
                br = self.get_neighbour_value_at(x+1,y+1,x,y)
                if tl and not(t) and not(l):
                    n += "k"
                if tr and not(t) and not(r):
                    n += "x"
                if bl and not(b) and not(l):
                    n += "y"
                if br and not(b) and not(r):
                    n += "z"
                cell.type = n
            else:
                cell.type = "s"
            for zoom, gm in enumerate(self.graphical_maps):
                if cell.type == "s":
                    type = "c"
                else:
                    type = cell.type
                gm[x,y].imgs = cell.couple.get_all_frames(zoom, type)



    def get_static_img_at_zoom(self, coord, zoom):
        """Returns the image contained on permanent cell of self.
        Use extract_img_at_zoom if you need the cell plus all what has been
        dynamically added (drawn) on self's surface."""
        if self.is_inside(coord):
            img = pygame.Surface((self.cell_sizes[0],)*2)
            self.extract_static_img_at_zoom(coord,zoom,img)
            return img
##            return self.graphical_maps[zoom][coord].imgs[self.t]
        else:
            return self.graphical_maps[zoom].outside_imgs[self.t]

    def extract_static_img_at_zoom(self, coord, zoom, img):
        """Returns the image of the cell of self plus what has been drawn on
        self's surface.
        Use get_static_img_at_zoom if you need the cell only."""
        if self.is_inside(coord):
            self.graphical_maps[zoom].extract_static_img(coord, self.t, img)
        else:
            img.blit(self.graphical_maps[zoom].outside_imgs[self.t],(0,0))



    def get_graphical_cell(self, coord, zoom):
        return self.graphical_maps[zoom][coord]


    def draw(self, screen, topleft, dx_pix, dy_pix):
        x0 = self.current_x
        y0 = self.current_y
        self.current_gm.draw(screen, topleft, x0, y0, dx_pix, dy_pix, self.t)

    def build_surfaces(self):
        for gm in self.graphical_maps:
            print("     Logical map building graphical map for size ",
                    gm.cell_size)
            gm.generate_submaps_parameters(factor=SUBMAP_FACTOR)
            gm.build_surfaces(self.colorkey)

    def reblit_material_of_cell(self, cell):
        for gm in self.graphical_maps:
            gm.reblit_material_of_cell(cell)

    def build_surfaces_fast(self):
        """Not that fast..."""
        ref = self.graphical_maps[0]
        ref.generate_submaps_parameters(factor=SUBMAP_FACTOR)
        ref.build_surfaces(self.colorkey)
        if len(self.graphical_maps) > 1:
            for gm in self.graphical_maps[1:]:
                gm.build_surfaces_from(self.colorkey, ref)

    def save_pure_surfaces(self):
        for gm in self.graphical_maps:
            gm.save_pure_surfaces()

    def reset_pure_surfaces(self):
        for gm in self.graphical_maps:
            gm.surfaces = gm.pure_surfaces
            gm.save_pure_surfaces()

    def blit_objects(self, objects=None, sort=True): #this is permanent
        if objects is None:
            objects = self.static_objects
        if sort:
            objects.sort(key=lambda x: x.ypos())
        for obj in objects:
            self.blit_object(obj)

    def blit_objects_only_on_cells(self, objs, cells):
        """Blit objs only on the specified cells, cropping the rest"""
        for o in objs:
            for c in cells:
                for level, gm in enumerate(self.graphical_maps):
                    gm.blit_object_only_on_cell(o,c)

    def blit_object(self, obj): #this is permanent
        """Permanently blit obj onto self's surfaces."""
        for level, gm in enumerate(self.graphical_maps):
            gm.blit_object(obj)



##    def show(self):
##        monitor.show()


class GraphicalMap(PygameGrid):

    def __init__(self, nx, ny, cell_size, level, actual_frame, outside_imgs):
##        cell_size = material_couples[0].get_cell_size(zoom_level)
        self.actual_frame = actual_frame
        PygameGrid.__init__(self, int(nx), int(ny),
                            cell_size=(cell_size,)*2,
                            topleft=actual_frame.topleft)
        self.level = level
        self.outside_imgs = outside_imgs
        self.cell_size = cell_size
        for coord in self:
            self[coord] = GraphicalCell()
        self.surfaces = None
        self.pure_surfaces = None #surfaces with no objects
        self.nframes = len(self.outside_imgs)
        #
        self.submap_size = None
        self.n_submaps = None

    def generate_submaps_parameters(self, factor):
        nsx, nsy = int(factor/self.cell_size), int(factor/self.cell_size)
        self.submap_size = (nsx*self.cell_size, nsy*self.cell_size)
        self.n_submaps = (math.ceil(self.frame.w/self.submap_size[0]),
                          math.ceil(self.frame.h/self.submap_size[1]))

    def build_surfaces(self, colorkey):
        #create table of surfaces
        surfaces = [[[pygame.Surface(self.submap_size) for frame in range(self.nframes)]
                        for y in range(self.n_submaps[1])]
                          for x in range(self.n_submaps[0])]
        #fill table of surfaces
        for x,y in self:
            surfx = x*self.cell_size//self.submap_size[0]
            surfy = y*self.cell_size//self.submap_size[1]
            xpix = x*self.cell_size - surfx*self.submap_size[0]
            ypix = y*self.cell_size - surfy*self.submap_size[1]
            for t in range(self.nframes):
                img = self[(x,y)].imgs[t]
                surfaces[surfx][surfy][t].blit(img, (xpix,ypix))
                if colorkey is not None:
                    surfaces[surfx][surfy][t].set_colorkey(colorkey)
        #
        self.surfaces = surfaces



    def reblit_material_of_cell(self, cell):
        """Blit the base surface (terrain)"""
        x,y = cell.coord
##        cell_object = self.get_cell_rect_at_coord_in_submap(cell.coord)
##        cell_object.inflate_ip((self.cell_size//3,)*2)
##        cell_here = self.get_cell_rect_at_coord_in_submap((x, y))
##        area_to_be_blitted = cell_here.clip(cell_object)
        surfx = x*self.cell_size//self.submap_size[0]
        surfy = y*self.cell_size//self.submap_size[1]
        xpix = x*self.cell_size - surfx*self.submap_size[0]
        ypix = y*self.cell_size - surfy*self.submap_size[1]
        for t in range(self.nframes):
            img = self[(x,y)].imgs[t]
            self.surfaces[surfx][surfy][t].blit(img, (xpix,ypix))


    def build_surfaces_from(self, colorkey, gm):
        factor = self.cell_size / gm.cell_size
        #we assume that ratio does not change bewteen submaps sizes of different zoom levels!
        scaled_size = (int(factor * gm.submap_size[0]),
                        int(factor * gm.submap_size[1]))
        #create table of surfaces
        surfaces = [[[None for frame in range(gm.nframes)]
                        for y in range(gm.n_submaps[1])]
                          for x in range(gm.n_submaps[0])]
        #fill table of surfaces
        for x in range(gm.n_submaps[0]):
            for y in range(gm.n_submaps[1]):
                for frame in range(gm.nframes):
                    resized = gm.surfaces[x][y][frame]
                    resized = pygame.transform.scale(resized, scaled_size)
                    surfaces[x][y][frame] = resized
        self.surfaces = surfaces
        self.submap_size = scaled_size
        self.n_submaps = gm.n_submaps
        self.nframes = gm.nframes

    def save_pure_surfaces(self):
        self.pure_surfaces = []
        for x in range(len(self.surfaces)):
            self.pure_surfaces.append([])
            for y in range(len(self.surfaces[0])):
                self.pure_surfaces[x].append([])
                for t in range(len(self.surfaces[0][0])):
                    self.pure_surfaces[x][y].append(None)
                    self.pure_surfaces[x][y][t] = self.surfaces[x][y][t].copy()


    def blit_object(self, obj):
        """blit images <obj_img> on self's surface"""
        relpos = obj.relpos
        xobj, yobj = obj.cell.coord
        obj_rect = obj.imgs_z_t[self.level][0].get_rect()
        obj_rect.center = (self.cell_size//2,)*2
        dx, dy = int(relpos[0]*self.cell_size), int(relpos[1]*self.cell_size)
        obj_rect.move_ip(dx,dy)
        #fill table of surfaces
        surfx = xobj*self.cell_size//self.submap_size[0]
        surfy = yobj*self.cell_size//self.submap_size[1]
        xpix = xobj*self.cell_size - surfx*self.submap_size[0] + obj_rect.x
        ypix = yobj*self.cell_size - surfy*self.submap_size[1] + obj_rect.y
        for dx in range(-1,2):
            for dy in range(-1,2):
                cx,cy = surfx+dx, surfy+dy
                if 0 <= cx < self.n_submaps[0] and 0 <= cy < self.n_submaps[1]:
                    x = xpix - dx*self.submap_size[0]
                    y = ypix - dy*self.submap_size[1]
                    for t in range(self.nframes):
                        img = obj.imgs_z_t[self.level][t%obj.nframes]
                        self.surfaces[cx][cy][t].blit(img, (x,y))


##    def blit_object_at(self, obj, x_cell, y_cell):
##        """blit image <obj_img> on self's surface, and only on the part of
##        self's surface belonging to the cell (x_cell,y_cell)."""
####        if o img_rect touch this cell's rect..., leave this fucking function !
####        obj_img_rect = obj.
##        #
##        relpos = obj.relpos
##        xobj, yobj = obj.cell.coord
##        obj_rect = obj.imgs_z_t[self.level][0].get_rect()
##        obj_rect.center = (self.cell_size//2,)*2
##        dx, dy = int(relpos[0]*self.cell_size), int(relpos[1]*self.cell_size)
##        obj_rect.move_ip(dx,dy)
##        #fill table of surfaces
##        # ######################################################################
##        #xpix_tot [pix] : location of xobj in the global map
##        #surfx [sub] : coord of the subsurface containing xobj
##        #xpix [pix] : location of xobj in the sub surface (local map)
##        xpix_tot = xobj*self.cell_size
##        ypix_tot = yobj*self.cell_size
##        surfx = xpix_tot//self.submap_size[0]
##        surfy = ypix_tot//self.submap_size[1]
##        xpix_sub = xpix_tot - surfx*self.submap_size[0] + obj_rect.x
##        ypix_sub = ypix_tot - surfy*self.submap_size[1] + obj_rect.y
##        # ######################################################################
##        #it is possible that the cell is spread on different subsurfaces !
##        #hence we loop :
##        for dx in range(-1,2): #not cell ! Just self's subsurfaces
##            for dy in range(-1,2): #not cell ! Just self's subsurfaces
##                cx, cy = surfx+dx, surfy+dy
##                #cx and cy are the subsurface coord of the current subsurface
##                #control that the subsurface exists:
##                if 0 <= cx < self.n_submaps[0] and 0 <= cy < self.n_submaps[1]:
##                    #x [pix]is the location of the obj image in the subsurface of coord cx,cy
##                    x = xpix_sub - dx*self.submap_size[0]
##                    y = ypix_sub - dy*self.submap_size[1]
##                    for t in range(self.nframes):
##                        img_obj = obj.imgs_z_t[self.level][t%obj.nframes]
##                        img_rect = img_obj.get_rect()
##                        img_rect.topleft = x,y
##                        cell_rect = self.get_cell_rect_at_coord_in_submap(obj.cell.coord)
##                        print("RECTs", img_rect, cell_rect)
##                        area_to_be_blitted = cell_rect.clip(img_rect)
##        ##                area_to_be_blitted = img_rect.clip(cell_rect)
##        ##                reste a rebouger en haut a gauche...
##                        area_to_be_blitted.move_ip((-x,-y))
##                        print("ATBB", area_to_be_blitted, img_rect)
##                        self.surfaces[cx][cy][t].blit(img_obj, (x+area_to_be_blitted.x,y+area_to_be_blitted.y), area_to_be_blitted)
##        ##                self.surfaces[cx][cy][t].blit(img_obj, (x,y))


    def blit_object_only_on_cell(self, obj, cell):
        """blit image <obj_img> on self's surface, and only on the part of
        self's surface belonging to the cell (x_cell,y_cell)."""
##        if o img_rect touch this cell's rect..., leave this fucking function !
        #First we deduce the absolute pos of the obj from its rel pos in the cell
        relpos = obj.relpos
        xobj, yobj = obj.cell.coord
        obj_rect = obj.imgs_z_t[self.level][0].get_rect()
        obj_rect.center = (self.cell_size//2,)*2
        dx, dy = int(relpos[0]*self.cell_size), int(relpos[1]*self.cell_size)
        obj_rect.move_ip(dx,dy)
        #fill table of surfaces
        # ######################################################################
        #xpix_tot [pix] : location of xobj in the global map
        #surfx [sub] : coord of the subsurface containing xobj
        #xpix [pix] : location of xobj in the sub surface (local map)
        xpix_tot = xobj*self.cell_size
        ypix_tot = yobj*self.cell_size
        surfx = xpix_tot//self.submap_size[0]
        surfy = ypix_tot//self.submap_size[1]
        xpix_sub = xpix_tot - surfx*self.submap_size[0] + obj_rect.x
        ypix_sub = ypix_tot - surfy*self.submap_size[1] + obj_rect.y
        # ######################################################################
##        cell_rect = self.get_cell_rect_at_coord_in_submap(cell.coord)
##        print("*** ", cell_rect, obj_rect)
##        if cell_rect.colliderect(obj_rect):
##            print("COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)
##        else:
##            print("     NOT COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)
##        return
        #it is possible that the cell is spread on different subsurfaces !
        #hence we loop :
        for dx in range(-1,2): #not cell ! Just self's subsurfaces
            for dy in range(-1,2): #not cell ! Just self's subsurfaces
                cx, cy = surfx+dx, surfy+dy
                #cx and cy are the subsurface coord of the current subsurface
                #control that the subsurface exists:
                if 0 <= cx < self.n_submaps[0] and 0 <= cy < self.n_submaps[1]:
                    #x [pix]is the location of the obj image in the subsurface of coord cx,cy
                    x = xpix_sub - dx*self.submap_size[0]
                    y = ypix_sub - dy*self.submap_size[1]
                    for t in range(self.nframes):
                        img_obj = obj.imgs_z_t[self.level][t%obj.nframes]
                        #ACCORDING TO ME, WE SHOULD CROP... But it seems to work anyway...
##                        img_rect = img_obj.get_rect()
##                        img_rect.topleft = x,y
##                        cell_rect = self.get_cell_rect_at_coord_in_submap(cell.coord)
##                        print("***", cell_rect, img_rect)
##                        if cell_rect.colliderect(obj_rect):
##                            print("COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)
##                        else:
##                            print("     NOT COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)

##                        return

##                        print("RECTs", img_rect, cell_rect)
##                        area_to_be_blitted = cell_rect.clip(img_rect)
##                        area_to_be_blitted = img_rect.clip(cell_rect)
##                        reste a rebouger en haut a gauche...
##                        area_to_be_blitted.move_ip((-x,-y))
##                        print("ATBB", area_to_be_blitted, img_rect)
##                        self.surfaces[cx][cy][t].blit(img_obj, (x+area_to_be_blitted.x,y+area_to_be_blitted.y), area_to_be_blitted)
                        self.surfaces[cx][cy][t].blit(img_obj, (x,y))

##FINALEMENT :
##    area to be blitted ne concerne que la partie de l'objet qui disparait qui chevauche les autres cellules.
##    Les autres cellules, donc, se redessinnent, mais on ne blitte que ca !


    def draw(self, screen, topleft, x0, y0, xpix, ypix, t):
        delta_x = topleft[0] - xpix - x0*self.cell_size
        delta_y = topleft[1] - ypix - y0*self.cell_size
        oldposx = delta_x
        for x in range(self.n_submaps[0]):
            posx = round(x*self.submap_size[0] + delta_x)
            for y in range(self.n_submaps[1]):
                posy = round(y*self.submap_size[1] + delta_y)
                screen.blit(self.surfaces[x][y][t], (posx,posy))

    def extract_static_img(self, coord, frame, img):
        """blit on <img> self's graphics present at <coord>"""
        cs = self.cell_size
        nx = int(200/cs)
        ny = int(200/cs)
        size_x = nx*cs
        size_y = ny*cs
        surfx = coord[0]*cs//size_x
        surfy = coord[1]*cs//size_y
        xpix = coord[0]*cs - surfx*size_x
        ypix = coord[1]*cs - surfy*size_y
        img.blit(self.surfaces[surfx][surfy][frame], (-xpix, -ypix))
##        if coord[1] == 7:
##            import thorpy
##            app = thorpy.get_application()
##            app.fill((255,255,255))
##            screen = thorpy.get_screen()
##            screen.blit(img, (0,0))
##            app.update()
##            print(xpix, ypix, coord)
##            app.pause()

    def get_cell_rect_at_coord_in_submap(self, cell_coord):
        xc,yc = cell_coord
        xpix_tot = xc*self.cell_size
        ypix_tot = yc*self.cell_size
        surfx = xpix_tot//self.submap_size[0]
        surfy = ypix_tot//self.submap_size[1]
        xpix_sub = xpix_tot - surfx*self.submap_size[0]
        ypix_sub = ypix_tot - surfy*self.submap_size[1]
        return pygame.Rect(xpix_sub,ypix_sub,self.cell_size,self.cell_size)


class WhiteLogicalMap(LogicalMap):

    def __init__(self, actual_frames, outsides, zoom_sizes, nframes,
                    restrict_size, white_value=(255,255,255)):
        self.zoom_levels = list(range(len(zoom_sizes)))
        self.current_zoom_level = 0
        self.cell_sizes = zoom_sizes
        self.actual_frames = actual_frames
        nx, ny = restrict_size
        BaseGrid.__init__(self, int(nx), int(ny))
        self.current_x = 0
        self.current_y = 0
        self.graphical_maps = []
        self.whites = []
        self.white_value = white_value
        for z in self.zoom_levels:
            cell_size = self.cell_sizes[z]
            gm = GraphicalMap(nx, ny, cell_size, z, actual_frames[z], outsides[z])
            self.graphical_maps.append(gm)
            white = pygame.Surface((cell_size,)*2)
            white.fill(self.white_value)
            self.whites.append(white)
        self.current_gm = self.graphical_maps[0]
        #
        self.nframes = nframes
        self.t = 0
        self.tot_time = 0
        self.frame_slowness = 20
        #
        self.refresh_cell_heights()
        self.refresh_cell_types()
        self.colorkey = white_value
        self.static_objects = []

    def refresh_cell_heights(self):
        for x,y in self:
            self[x,y] = WhiteLogicalCell(self)

    def refresh_cell_types(self):
        for x,y in self:
            cell = self[x,y]
            for zoom_level, gm in enumerate(self.graphical_maps):
                gm[x,y].imgs = [self.whites[zoom_level] for i in range(self.nframes)]
