import pygame
from pygame.math import Vector2 as V2
from PyWorld2D.gui.parameters import RMOUSE_COLOR


##DELTA_STATIC_OBJECTS = [(1,0),(-1,0),(0,-1),(0,1),(0,0),
##                        (1,1), (-1,1), (1,-1), (-1,-1)]
DELTA_STATIC_OBJECTS = [(1,0),(-1,0),(0,-1),(0,1),(0,0)]
class Camera:

    def __init__(self):
        self.lm = None
        self.cell_rect = pygame.Rect(0,0,0,0)
        self.e_hmap = None
        self.box_hmap = None
        self.campos = V2()
        self.rcam = None
        self.rmouse = None
        self.world_size = V2()
        self.nx, self.ny = 0, 0
        self.img_hmap = None
        self.ui_manager = None
        self.me = None

    def set_parameters(self, world_size, cell_size, viewport_rect, img_hmap, max_minimap_size):
        ws, img = get_world_and_minimap_sizes(img_hmap, max_minimap_size)
        self.img_hmap = img
        ms = self.img_hmap.get_size()
        self.world_size = V2(world_size)
        self.cell_rect.size = (cell_size,)*2
        self.nx = viewport_rect.w//self.cell_rect.w - 1 #number of cells along x
        self.ny = viewport_rect.h//self.cell_rect.h - 1
        map_size = self.nx*self.cell_rect.w, self.ny*self.cell_rect.h
        self.map_rect = pygame.Rect((0,0), map_size)
        self.map_rect.center = viewport_rect.center
        self.rcam = pygame.Rect(0,0,self.nx,self.ny) #in cell_units
        w = int(self.nx*ms[0]/self.world_size.x)
        h = int(self.ny*ms[1]/self.world_size.y)
        self.rmouse = pygame.Rect(0,0,w,h) #rect on minimap (hmap)


    def reinit_pos(self):
        self.rmouse.topleft = self.e_hmap.get_rect().topleft
        self.set_campos_from_rcam()

    def set_gui_elements(self, e_hmap, box_hmap):
        self.e_hmap = e_hmap
        self.box_hmap = box_hmap
        self.reinit_pos()

    def draw_rmouse(self, screen, clipping):
        rect = self.rmouse.clip(clipping)
        screen.set_clip(rect)
        pygame.draw.rect(screen, RMOUSE_COLOR, self.rmouse, 1)
        screen.set_clip()

    def set_map_data(self, lm):
        self.lm = lm
        assert lm.nx == self.world_size.x and lm.ny == self.world_size.y

    def get_dpix(self):
        """Returns the offset within the current cell"""
        x = (self.campos.x - self.rcam.x)*self.cell_rect.w
        y = (self.campos.y - self.rcam.y)*self.cell_rect.h
        return x,y

    def draw_grid(self, screen, show_grid_lines):
        xpix, ypix = self.get_dpix()
        import time
        self.lm.draw(screen, self.map_rect.topleft, xpix, ypix)
        if show_grid_lines:
            self.draw_grid_lines(screen)

    def draw_grid_lines(self, screen):
        coord = self.get_coord_at_pix(self.map_rect.topleft+V2(1,1))
        xpix, ypix = self.get_rect_at_coord(coord).topleft
        for x in range(self.nx+1):
            p1 = (xpix, self.map_rect.top-20)
            p2 = (xpix, self.map_rect.bottom+20)
            pygame.draw.line(screen, (0,0,0), p1, p2)
            xpix += self.cell_rect.w
        for y in range(self.ny+1):
            p1 = (self.map_rect.left-20, ypix)
            p2 = (self.map_rect.right+20, ypix)
            pygame.draw.line(screen, (0,0,0), p1, p2)
            ypix += self.cell_rect.h

    def set_mg_pos_from_rcam(self):
        self.lm.current_x = int(self.rcam.x)
        self.lm.current_y = int(self.rcam.y)

    def set_campos_from_rcam(self):
        self.campos = V2(self.rcam.topleft)

    def set_rcam_from_campos(self):
        self.rcam.topleft = self.campos

    def set_rcam_from_rmouse(self):
        rminimap = self.e_hmap.get_rect()
        self.rcam.x = (self.rmouse.x - rminimap.x)*self.world_size.x/rminimap.w
        self.rcam.y = (self.rmouse.y - rminimap.y)*self.world_size.y/rminimap.h

    def set_rmouse_from_rcam(self):
        rminimap = self.e_hmap.get_rect()
        self.rmouse.x = self.rcam.x*rminimap.w/self.world_size.x + rminimap.x
        self.rmouse.y = self.rcam.y*rminimap.h/self.world_size.y + rminimap.y
##        print("rcam.x =",self.rcam.x, "  world size x = ",self.world_size.x)
##        print("     rminimap.w=", rminimap.w, "ratio1", (self.rmouse.x-rminimap.x)/rminimap.w,
##                                            "ratio2", (self.rcam.x/self.world_size.x))

    def move(self, delta):
##        print("***", delta)
##        coord = (0,0)
##        x1,y1 = self.get_rect_at_coord(coord).topleft
        self.campos += delta
        self.set_rcam_from_campos()
##        x2,y2 = self.get_rect_at_coord(coord).topleft
##        delta = (x2-x1, y2-y1)
##        print("     ", delta)
##        self.me.game.translate_smokes(delta)
        self.me.game.recompute_smokes_position()

    def get_cell(self, pix):
##        if self.map_rect.collidepoint(pix):
        if not self.me.e_box.get_fus_rect().collidepoint(pix):
            coord = self.get_coord_at_pix(pix)
            if self.lm.is_inside(coord):
                return self.lm[coord]

    def center_on(self, minimap_pos):
        """Units : pixels on minimap."""
        if self.box_hmap.get_rect().collidepoint(minimap_pos):
            self.rmouse.center = minimap_pos
            self.set_rcam_from_rmouse()
            self.set_mg_pos_from_rcam()
            self.set_campos_from_rcam()

    def center_on_cell(self, coord):
        self.rcam.center = coord
        self.set_rmouse_from_rcam()
        self.set_mg_pos_from_rcam()
        self.set_campos_from_rcam()


    def correct_move(self, d):
        dx, dy = d
        lm = self.lm
        if lm.current_x + self.nx > lm.nx + 2 and dx > 0:
            dx = 0
        elif lm.current_x < -2 and dx < 0:
            dx = 0
        if lm.current_y + self.ny > lm.ny + 2 and dy > 0:
            dy = 0
        elif lm.current_y < -2 and dy < 0:
            dy = 0
        return dx, dy

    def get_rect_at_coord(self, coord):
        dx, dy = self.get_dpix()
        shift_x = (coord[0] - self.lm.current_x) * self.cell_rect.w - int(dx)
        shift_y = (coord[1] - self.lm.current_y) * self.cell_rect.h - int(dy)
        return self.cell_rect.move((shift_x, shift_y)).move(self.map_rect.topleft)

    def get_coord_at_pix(self, pix):
        pos = V2(self.get_dpix()) - self.map_rect.topleft + pix
        pos.x *= self.nx/self.map_rect.w
        pos.y *= self.ny/self.map_rect.h
        #now pos represents the exact (not integer) coord relative to the first displayed coord !
        deltax, deltay = 0, 0
        if pos.x < 0:
            deltax = -1
        if pos.y < 0:
            deltay = -1
        return (int(pos.x) + self.lm.current_x + deltax,
                int(pos.y) + self.lm.current_y + deltay)

    def get_rect_at_pix(self, pix):
        return self.get_rect_at_coord(self.get_coord_at_pix(pix))

    def log_static_objects_around(self, o, to_sort, drawn_last):
        """Blit the neighboring objects according to their y-coordinate."""
        x,y = o.cell.coord
        s = self.lm.get_current_cell_size()
        for dx,dy in DELTA_STATIC_OBJECTS: #includes 4 neighs + (0,0)
            cell = self.lm.get_cell_at(x+dx, y+dy)
            if cell:
                r = self.get_rect_at_coord(cell.coord)
                for so in cell.objects:
                    if so is not o:
                        if not so.is_ground: #if ground no need to reblit
                            so_rect, so_img = so.get_fakerect_and_img(s)
                            if so.always_drawn_last:
                                drawn_last.add((so_rect,so_img,so))
                            else:
                                to_sort.add((so_rect,so_img,so))

    #How it works:
    #   We collect all the objects to be drawn, plus the static objects around them.
    #   Then, we sort this big list by rect bottom coord, and we draw them.
    def draw_objects(self, screen, objs, draw_ui):
        s = self.lm.get_current_cell_size()
        if draw_ui:
            self.ui_manager.draw_before_objects(s)
        to_sort = set()
        drawn_last = set()
        force_drawn_first = set()
        for o in objs:
            if o.hide:
                continue
            rect, img = o.get_fakerect_and_img(s)
            if o.always_drawn_last:
                drawn_last.add((rect,img,o))
            else:
                if o.is_ground:
                    force_drawn_first.add((rect,img,o))
                elif "bridge" in o.str_type:
                    force_drawn_first.add((rect,img,o))
                else:
                    to_sort.add((rect,img,o))
            self.log_static_objects_around(o, to_sort, drawn_last)
        ########################################################################
        force_drawn_first = [(img,rect) for rect,img,o in force_drawn_first if not o.hide]
        drawn_second = [(img,rect) for rect,img,o in to_sort if not o.hide]
        drawn_second.sort(key=lambda x:x[1][3])
        drawn_last = [(img,rect) for rect,img,o in drawn_last if not o.hide]
        screen.blits(force_drawn_first)
        screen.blits(drawn_second)
        screen.blits(drawn_last)
        if draw_ui:
            self.ui_manager.draw_after_objects(s)


    def get_center_coord(self):
        return self.get_coord_at_pix(self.map_rect.center)


def get_world_and_minimap_sizes(img_hmap, max_minimap_size):
    world_size = img_hmap.get_size() #can differ from hmap size!
    w,h = world_size
    if w >= h and w > max_minimap_size[0]:
        M = max_minimap_size[0]
        size_y = int(max_minimap_size[1]*h/w)
        img_hmap = pygame.transform.smoothscale(img_hmap, (M,size_y))
    elif w < h and h > max_minimap_size[1]:
        M = max_minimap_size[1]
        size_x = int(max_minimap_size[0]*w/h)
        img_hmap = pygame.transform.smoothscale(img_hmap, (size_x,M))
    #minimap_size can differ from world_size !
    return world_size, img_hmap
