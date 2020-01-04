import pygame, thorpy, math
import PyWorld2D.gui.elements as elements
import PyWorld2D.gui.parameters as guip

from logic.battle import Battle, DistantBattle
from logic.unit import DELTA_TO_KEY, DELTAS

class Footprint:

    def __init__(self, unit, age, pos):
        self.unit = unit
        dx = self.unit.footprint.get_size()[0]
        self.age = age
        self.pos = (pos[0]-dx,pos[1]-dx)
        self.pos2 = (pos[0]+dx, pos[1]+dx)

    def blit_and_increment(self, surface):
        surface.blit(self.unit.footprint, self.pos)
        surface.blit(self.unit.footprint, self.pos2)
        self.age += 1


class GuiGraphicsEnhancement:

    def __init__(self, gui, zoom, splashes=True, footprints=True):
        self.zoom = zoom
        self.gui = gui
        self.surface = self.gui.surface
        #
        self.splashes = []
        self.splash = None
        self.units_splashes = []
        if splashes:
            self.splashes = [pygame.image.load("sprites/splash.png")]
            self.splashes.append(pygame.transform.flip(self.splashes[0],
                                    True, False))
            self.splash = self.splashes[0]
        #
        self.show_footprints = footprints
        self.footprints = {}
        self.max_footprint_age = 100

    def draw_splashes(self):
        if self.gui.game.me.zoom_level != self.zoom:
            return
        self.splash = self.splashes[self.gui.game.me.lm.t%len(self.splashes)]
        for u in self.units_splashes:
            rect = u.get_current_rect(self.zoom)
            self.surface.blit(self.splash, rect.move(0,-6).bottomleft)

    def draw_footprints(self):
        if self.gui.game.me.zoom_level != self.zoom:
            return
        to_remove = []
        for coord, footprint in self.footprints.items():
            if footprint.age > self.max_footprint_age:
                to_remove.append(coord)
            else:
                footprint.blit_and_increment(self.surface)
        for coord in to_remove:
            self.footprints.pop(coord)


    def refresh(self):
        if self.gui.game.me.zoom_level != self.zoom:
            return
        if self.splash or self.show_footprints:
            self.units_splashes = []
            for u in self.gui.game.units:
                t = u.get_terrain_name_for_fight()
                ############################ Splashes ##########################
                if self.splash:
                    if t == "river" or "water" in t:
                        self.units_splashes.append(u)
                ################### Footprints #################################
                if self.show_footprints:
                    if t == "sand" or "snow" in t:
                        rect = u.get_current_rect(self.zoom)
                        footprint = Footprint(u, 0, rect.center)
                        self.footprints[u.cell.coord] = footprint







class Gui:

    def __init__(self, game):
        self.game = game
        self.surface = thorpy.get_screen()
        game.me.cam.ui_manager = self
        self.me = game.me
        self._debug = True
        self.enhancer = GuiGraphicsEnhancement( self, zoom=0, #work only for a given zoom level
                                                splashes=True,
                                                footprints=True)
        self.lifes = []
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
        self.add_reactions()
        self.font_life = pygame.font.SysFont(guip.font_gui_life, guip.NFS)
        self.refresh_lifes()
        self.show_lifes = True

    def clear(self):
        self.selected_unit = None
        self.unit_under_cursor = None
        self.blue_highlights = []
        self.red_highlights = []

    def get_destinations(self, cell):
        destinations = []
        self.red_highlights = []
        self.blue_highlights = []
        if cell.unit:
            if cell.unit.is_object:
                return []
            if cell.unit.anim_path: #moving unit, let her alone...
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

    def go_to_cell(self, u, path):
        u.move_to_cell_animated(path)
        self.moving_units.append(u)
        self.game.walk_sounds[0].play(-1)

    def refresh_moving_units(self):
        to_remove = []
        for u in self.moving_units:
            if not u.anim_path:
                to_remove.append(u)
        for u in to_remove:
            self.moving_units.remove(u)
            self.game.walk_sounds[0].stop()


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
                        self.go_to_cell(self.selected_unit, path[1:])
                    else:
                        self.add_alert(self.e_cant_move)
                        self.game.deny_sound.play()
                else:
                    self.go_to_cell(self.selected_unit, path[1:])
            else:
                self.add_alert(self.e_cant_move_another)
                self.game.deny_sound.play()
            # self.selected_unit.move_to_cell(cell)
            self.selected_unit = None

    def treat_click_interaction(self, unit):
        if unit in self.red_highlights: #then self.selected_unit is the agressor
            defender = unit
            dx = defender.cell.coord[0] - self.selected_unit.cell.coord[0]
            dy = defender.cell.coord[1] - self.selected_unit.cell.coord[1]
            distance = abs(dx)+abs(dy)
            b = None
            if distance > 1 and self.selected_unit.attack_range[1] >= distance: #distant attack
                units_in_battle = [self.selected_unit, defender]
                b = DistantBattle(self.game, units_in_battle, defender, distance)
            elif distance == 1:
                units_in_battle = defender.get_all_surrounding_ennemies()
                units_in_battle.append(defender)
                b = Battle(self.game, units_in_battle, defender, distance)
            if b:
                b.fight()
                self.clear()
                thorpy.get_current_menu().fps = guip.FPS
                self.refresh_lifes()
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

    def refresh_lifes(self):
        self.lifes = []
        for u in self.game.units:
            if not u in self.moving_units:
                text = self.font_life.render(str(u.quantity), True, (0,0,0))
                x,y = self.game.me.cam.get_rect_at_coord(u.cell.coord).center
                coord = x+4,y+4
                self.lifes.append((text, coord))

    def draw_before_objects(self, s):
        self.enhancer.draw_footprints()
        self.refresh_moving_units()
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
        self.enhancer.draw_splashes()
        if self.show_lifes:
            self.refresh_lifes()
            for img, coord in self.lifes:
                self.surface.blit(img, coord)

    def refresh(self):
        self.enhancer.refresh()

##    def add_flag(self):
##        self.game.add_unit((16,15), self.game.units[0].race["flag"], 1, team=self.game.units[0].team)

    def toggle_show_life(self):
        self.show_lifes = not(self.show_lifes)

    def add_reactions(self):
        reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, self.lmb,{"button":1})
        self.me.e_box.add_reaction(reac_click)
        reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, self.rmb,{"button":2})
        self.me.e_box.add_reaction(reac_click)
        reac_motion = thorpy.Reaction(pygame.MOUSEMOTION, self.mousemotion)
        self.me.e_box.add_reaction(reac_motion)
##        reac_escape = thorpy.ConstantReaction(pygame.KEYDOWN, self.esc_menu, {"key":pygame.K_ESCAPE})
##        self.me.e_box.add_reaction(reac_escape)
        shortcuts = [(pygame.K_l, self.toggle_show_life)]
        reacs = []
        for key,func in shortcuts:
            reacs.append(thorpy.ConstantReaction(pygame.KEYDOWN, func,
                         {"key":key}))
        self.me.e_box.add_reactions(reacs)


