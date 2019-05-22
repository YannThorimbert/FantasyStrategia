import pygame, thorpy, math
import PyWorld2D.gui.elements as elements
import PyWorld2D.gui.parameters as guip

class Gui:

    def __init__(self, me):
        self.surface = thorpy.get_screen()
        me.cam.ui_manager = self
        self.me = me
        #
        self.last_destination_score = {}
        self.destinations_mousemotion = []
        self.destinations_lmb = []
        self.selected_unit = None
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
        if cell.unit:
            score = cell.unit.get_possible_destinations()
            self.last_destination_score = score
            self.selected_unit = cell.unit
            for coord in score:
                v = score[coord]
                rect = self.me.cam.get_rect_at_coord(coord)
                destinations.append(rect.topleft)
        return destinations

    def add_alert(self, e):
        self.me.ap.add_alert(e, guip.DELAY_HELP * self.me.fps)

    def lmb(self, e):
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if self.destinations_lmb: #then the user may be clicking a destination
            rect = self.me.cam.get_rect_at_coord(cell.coord)
            if rect.topleft in self.destinations_lmb:
                if not cell.unit: #then move the unit
                    self.selected_unit.move_to_cell(cell)
                    self.selected_unit = None
                else:
                    self.add_alert(self.e_cant_move)
            self.destinations_lmb = {} #clear destinations
        elif cell: #else update destinations
            self.destinations_lmb = self.get_destinations(cell)

    def mousemotion(self, e):
        self.destinations_mousemotion = {}
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            self.destinations_mousemotion = self.get_destinations(cell)

    def get_alpha_dest(self):
        t = self.me.lm.tot_time
        return math.sin(t * self.dest_omega) * self.dest_alpha_amplitude + self.dest_alpha0

    def draw_before_objects(self, s):
        surf = pygame.Surface((s,s))
        surf.set_alpha(self.get_alpha_dest())
        if not self.destinations_lmb:
            surf.fill(self.color_dest_mousemotion)
            for pos in self.destinations_mousemotion:
                self.surface.blit(surf, pos)
        else:
            surf.fill(self.color_dest_lmb)
            for pos in self.destinations_lmb:
                self.surface.blit(surf, pos)

    def draw_after_objects(self, s):
        pass
