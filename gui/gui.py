import pygame, thorpy, math
import PyWorld2D.gui.elements as elements
import PyWorld2D.gui.parameters as guip

from logic.battle import Battle
from logic.unit import DELTA_TO_KEY, DELTAS


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
        self.e_cant_move_another = guip.get_highlight_text("Another unit is already going there")
        #
        self.moving_units = []

    def get_destinations(self, cell):
        destinations = []
        self.red_highlights = []
        self.blue_highlights = []
        if cell.unit:
            if cell.unit.anim_path:
                return []
            if not self.selected_unit:
                ref_unit = self.unit_under_cursor
            else:
                ref_unit = self.selected_unit
            score = cell.unit.get_possible_destinations()
            score[cell.coord] = []
            self.last_destination_score = score
            for coord in score:
##                if coord != cell.coord:
                rect = self.me.cam.get_rect_at_coord(coord)
                destinations.append(rect.center)
                if ref_unit:
                    self.update_possible_interactions(ref_unit, coord)
        return destinations

    def update_possible_interactions(self, ref_unit, coord):
        #interactions possible for <ref_unit> when located at hypothetic position <coord>
        for other in self.game.units:
            if other is not ref_unit:
                if other.cell.coord == coord:
                    self.add_unit_highlight(ref_unit, other)
                else:
                    if other.team == ref_unit.team:
                        coords = ref_unit.get_coords_in_help_range()
                    else:
                        coords = ref_unit.get_coords_in_attack_range()
                    for dx,dy in coords:
                        if other.cell.coord == (coord[0]+dx, coord[1]+dy):
                            self.add_unit_highlight(ref_unit, other)
                            break


    def add_unit_highlight(self, ref_unit, unit):
        if unit.team == ref_unit.team:
            self.blue_highlights.append(unit)
        else:
            self.red_highlights.append(unit)

    def add_alert(self, e):
        self.me.ap.add_alert(e, guip.DELAY_HELP * self.me.fps)


    def treat_click_destination(self, cell):
        rect = self.me.cam.get_rect_at_coord(cell.coord)
        print("     clicked:", cell.coord)
        print("     len(dest_lmb):", len(self.destinations_lmb))
        if rect.center in self.destinations_lmb:
            print("     Correct destination")
            cost, path = self.last_destination_score.get(cell.coord, None)
            x,y = path[-1]
            friend = self.game.get_unit_at(x,y)
            print("     friend:",friend)
            #control that the path is not crossing another moving unit's path..
            can_move = True
            for u in self.moving_units:
                if not(u is self.selected_unit):
                    for planned_coord in u.anim_path:
                        if planned_coord in path:
                            can_move = False
                            break
            if can_move:
                if friend: #the user wants to fusion units
                    #check that same type and sum of quantities does not exceed max_quantity
                    ok = False
                    if ok:
                        self.selected_unit.move_to_cell_animated(path[1:])
                        self.moving_units.append(self.selected_unit)
                    else:
                        self.add_alert(self.e_cant_move)
                else:
                    self.selected_unit.move_to_cell_animated(path[1:])
                    self.moving_units.append(self.selected_unit)
            else:
                self.add_alert(self.e_cant_move_another)
            # self.selected_unit.move_to_cell(cell)
            self.selected_unit = None

    def treat_click_interaction(self, unit):
        if unit in self.red_highlights:
            defender = unit
            dx = defender.cell.coord[0] - self.selected_unit.cell.coord[0]
            dy = defender.cell.coord[1] - self.selected_unit.cell.coord[1]
            delta = DELTA_TO_KEY.get((dx,dy))
            if delta is not None:
                units_in_battle = defender.get_all_surrounding_units()
                units_in_battle.append(defender)
                #here, interact with user to select actual participating units among candidates to battle
                print("DEFENDER", defender, defender.team, defender.quantity)
                b = Battle(self.game, units_in_battle, defender)
                b.fight()
        elif unit in self.blue_highlights:
            pass
        else:
            self.add_alert(self.e_cant_move)


    def lmb(self, e):
        print("LMB", self.game.t)
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            if self.destinations_lmb: #then the user may be clicking a destination
                if not cell.unit:
                    print("click destination")
                    self.treat_click_destination(cell)
                else:
                    print("treat interaction")
                    self.treat_click_interaction(cell.unit)
                self.destinations_lmb = [] #clear destinations
                self.red_highlights = []
                self.blue_highlights = []
                self.selected_unit = None
            elif cell: #else update destinations
                if cell.unit:
                    print("update destinations")
                    self.selected_unit = cell.unit
                    self.destinations_lmb = self.get_destinations(cell)
                else:
                    print("nothing")
                    self.selected_unit = None


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
