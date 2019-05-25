import pygame, thorpy, math
import PyWorld2D.gui.elements as elements
import PyWorld2D.gui.parameters as guip


class Gui:

    def __init__(self, game):
        self.game = game
        self.surface = thorpy.get_screen()
        game.me.cam.ui_manager = self
        self.me = game.me
        self._debug = True
        #
        self.last_destination_score = {}
        self.destinations_mousemotion = []
        self.destinations_lmb = []
        self.selected_unit = None
        self.unit_under_cursor = None
        self.blue_highlights = []
        self.red_highlights = []
        #
        self.color_dest_lmb = (255,0,0)
        self.color_dest_mousemotion = (255,255,0)
        self.dest_alpha_amplitude = 20
        self.dest_alpha0 = 100
        self.dest_period = self.me.lm.nframes * 3.
        self.dest_omega = 2. * math.pi / self.dest_period
        #
        self.e_cant_move = guip.get_highlight_text("Can't go there")

    def get_destinations(self, cell):
        destinations = []
        self.red_highlights = []
        self.blue_highlights = []
        if cell.unit:
            if cell.unit.anim_path:
                return []
            score = cell.unit.get_possible_destinations()
            self.last_destination_score = score
            for coord in score:
                if coord != cell.coord:
                    rect = self.me.cam.get_rect_at_coord(coord)
                    destinations.append(rect.center)
                    #
                    ref_unit = self.selected_unit
                    if not self.selected_unit:
                        ref_unit = self.unit_under_cursor
                    if ref_unit:
                        self.update_possible_interactions(ref_unit, coord)
        return destinations

    def update_possible_interactions(self, ref_unit, coord):
        for unit in self.game.units:
            if unit is not ref_unit:
                if unit.cell.coord == coord:
                    self.add_unit_highlight(ref_unit, unit)
                else:
                    if unit.team == ref_unit.team:
                        coords = ref_unit.get_coords_in_help_range()
                    else:
                        coords = ref_unit.get_coords_in_attack_range()
                    for dx,dy in coords:
                        if unit.cell.coord == (coord[0]+dx, coord[1]+dy):
                            self.add_unit_highlight(ref_unit, unit)


    def add_unit_highlight(self, ref_unit, unit):
        if unit.team == ref_unit.team:
            self.blue_highlights.append(unit)
        else:
            self.red_highlights.append(unit)

    def add_alert(self, e):
        self.me.ap.add_alert(e, guip.DELAY_HELP * self.me.fps)

    def lmb(self, e):
        self.red_highlights = []
        self.blue_highlights = []
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            if self.destinations_lmb: #then the user may be clicking a destination
                rect = self.me.cam.get_rect_at_coord(cell.coord)
                if rect.center in self.destinations_lmb:
                    if not cell.unit: #then move the unit
                        cost, path = self.last_destination_score.get(cell.coord, None)
                        x,y = path[-1]
                        friend = self.game.get_unit_at(x,y)
                        if friend:
                            #check than same type and sum of quantities does not exceed max_quantity
                            ok = False
                            if ok:
                                self.selected_unit.move_to_cell_animated(path[1:])
                            else:
                                self.add_alert(self.e_cant_move)
                        else:
                            self.selected_unit.move_to_cell_animated(path[1:])
                        # self.selected_unit.move_to_cell(cell)
                        self.selected_unit = None
                    else:
                        self.add_alert(self.e_cant_move)
                self.destinations_lmb = [] #clear destinations
                self.selected_unit = None
            elif cell: #else update destinations
                self.destinations_lmb = self.get_destinations(cell)
                if cell.unit:
                    self.selected_unit = cell.unit

    def rmb(self, e):
        self.destinations_mousemotion = []
        self.destinations_lmb = []
        self.selected_unit = None

    def mousemotion(self, e):
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            if cell.unit:
                self.unit_under_cursor = cell.unit
            else:
                self.unit_under_cursor = None
            if self.destinations_lmb: #then the user may be tracing the path
                value = self.last_destination_score.get(cell.coord, None)
                if value:
                    cost, path = value
                    for coord in path:
                        rect = self.me.cam.get_rect_at_coord(coord)
                        self.destinations_mousemotion.append(rect.center)
            else:
                self.destinations_mousemotion = self.get_destinations(cell)

    def get_alpha_dest(self):
        t = self.me.lm.tot_time
        return math.sin(t * self.dest_omega) * self.dest_alpha_amplitude + self.dest_alpha0

    def draw_highlight(self, unit, color, s):
        img = unit.get_current_highlight(color)
        rect = img.get_rect()
        rect.center = unit.get_current_rect_center(s)
        self.surface.blit(img, rect.topleft)

    def draw_before_objects(self, s):
        if self.unit_under_cursor:
            self.draw_highlight(self.unit_under_cursor, "yellow", s)
        if self.selected_unit:
            if self.selected_unit is not self.unit_under_cursor:
                self.draw_highlight(self.selected_unit, "yellow", s)
        #1. left mouse button
        if self.destinations_lmb:
            surf = pygame.Surface((s,s))
            rect = surf.get_rect()
            surf.set_alpha(self.get_alpha_dest())
            surf.fill(self.color_dest_lmb)
            for pos in self.destinations_lmb:
                rect.center = pos
                self.surface.blit(surf, rect)
        #2. mousemotion
        if self.destinations_mousemotion:
            surf = pygame.Surface((s-2,s-2))
            rect = surf.get_rect()
            surf.set_alpha(self.get_alpha_dest())
            surf.fill(self.color_dest_lmb)
            surf.fill(self.color_dest_mousemotion)
            for pos in self.destinations_mousemotion:
                rect.center = pos
                self.surface.blit(surf, rect)
                if self._debug:
                    coord = self.me.cam.get_coord_at_pix(rect.center)
                    #debug : draw distance
##                    if coord in self.last_destination_score:
##                        cost = self.last_destination_score[coord][0]
##                        text = thorpy.make_text(str(cost))
##                        self.surface.blit(text.get_image(), rect)
        for unit in self.red_highlights:
            self.draw_highlight(unit, "red", s)
        for unit in self.blue_highlights:
            self.draw_highlight(unit, "blue", s)

    def draw_after_objects(self, s):
        pass
