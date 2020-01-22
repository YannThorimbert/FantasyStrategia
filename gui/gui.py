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
        self.cell_under_cursor = None
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
        self.life_font_size = guip.NFS
        self.life_font_color = (0,0,0)
        self.font_life = pygame.font.SysFont(guip.font_gui_life, self.life_font_size)
        self.refresh_lifes()
        self.show_lifes = True
        self.actions = {"flag":[("Remove flag",self.remove_flag,
                                    self.check_interact_flag),
                                ("Replace flag",self.set_flag,
                                    self.check_interact_flag)]
                        }
        self.actions_no_objs = [("Plant flag",self.set_flag,
                                    self.check_interact_flag),
                                ("Burn",self.burn,
                                    self.check_interact_burn)]
        self.interaction_objs = []

    def refresh_graphics_options(self):
        self.font_life = pygame.font.SysFont(guip.font_gui_life, self.life_font_size)
        self.clear()

    def check_interact_burn(self):
        """Return True if there is at least one thing (cell/object) that can
        burn."""
        if self.game.burning.get(self.cell_under_cursor.coord):
            return False
        elif self.unit_under_cursor():
            return False
        elif self.selected_unit.cell.distance_to(self.cell_under_cursor) != 1:
            return False
        else:
            for o in self.cell_under_cursor.objects:
                if o.name in self.game.is_burnable:
                    return True
            for o in self.cell_under_cursor.objects:
                if o.name == "river":
                    return False
        return self.cell_under_cursor.material.name.lower() in self.game.is_burnable


    def check_interact_flag(self):
        c = self.cell_under_cursor
        if self.game.burning.get(c.coord):
            return False
        if c.unit:
            if c.unit.team != self.selected_unit.team:
                return False
        if self.selected_unit.cell.distance_to(c) <= 1:
            return c.material.name.lower() in self.game.is_flaggable

    def clear(self):
        self.selected_unit = None
        self.cell_under_cursor = None
        self.blue_highlights = []
        self.red_highlights = []
        self.interaction_objs = []

    def get_destinations(self, cell):
        destinations = []
        self.red_highlights = []
        self.blue_highlights = []
        if cell.unit:
            if cell.unit.anim_path: #moving unit, let her alone...
                return []
            if not self.selected_unit:
                ref_unit = self.cell_under_cursor.unit
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



    def attack(self):
##        defender = self.interaction_objs[0].cell.unit
        defender = self.unit_under_cursor()
        distance = defender.distance_to(self.selected_unit)
        units_in_battle = defender.get_all_surrounding_ennemies()
        units_in_battle.append(defender)
        b = Battle(self.game, units_in_battle, defender, distance)
        b.fight()
        self.clear()
        thorpy.get_current_menu().fps = guip.FPS
        self.refresh_lifes()

    def distant_attack(self):
        defender = self.unit_under_cursor()
        distance = defender.distance_to(self.selected_unit)
        units_in_battle = [self.selected_unit, defender]
        b = DistantBattle(self.game, units_in_battle, defender, distance)
        b.fight()
        self.clear()
        thorpy.get_current_menu().fps = guip.FPS
        self.refresh_lifes()

    def remove_flag(self):
        for o in self.interaction_objs:
            if o.type_name == "flag":
                o.remove_from_game()
                break

    def set_flag(self):
        self.remove_flag()
        cell = self.cell_under_cursor
        self.game.add_object(cell.coord, self.selected_unit.race.flag, 1)

    def burn(self):
        self.game.set_fire(self.cell_under_cursor.coord, 2)

    def help(self, unit):
        print("Not implemented yet")
        pass

    def get_interaction_choices(self, objs):
        choices = {}
        cell = self.cell_under_cursor
        d = cell.distance_to(self.selected_unit.cell)
        if objs:
            if cell.unit and not(self.selected_unit is cell.unit):
                other = cell.unit
                if cell.unit in self.red_highlights: #then self.selected_unit is the agressor
                    if d > 1 and self.selected_unit.attack_range[1] >= d: #distant attack
                        choices["Distant attack"] = self.distant_attack
                    elif d == 1:
                        choices["Attack"] = self.attack
                elif cell.unit in self.blue_highlights:
                    if d > 1 and self.selected_unit.help_range[1] >= d: #distant attack
                        choices["Distant help"] = self.help
                    elif d == 1:
                        choices["Help"] = self.help
            for o in objs:
                if o != cell.unit:
                    for name, func, check in self.actions.get(o.type_name):
                        if check():
                            choices[name] = func
            self.interaction_objs = objs
        for name, func, check in self.actions_no_objs:
            if check():
                choices[name] = func
        return choices


    def user_make_choice(self, choices):
        choice = thorpy.launch_blocking_choices_str("Choose an action",
                                                    sorted(choices.keys())+["Cancel"],
                                                    title_fontsize=guip.NFS,
                                                    title_fontcolor=guip.NFC)
        func = choices.get(choice, None)
        if func:
            func()
##        treat outside click to cancel
        self.clear()


    def lmb(self, e):
        print("LMB", self.game.t)
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            if self.destinations_lmb: #then the user may be clicking a destination
                interactibles = self.game.get_interactive_objects( cell.coord[0],
                                                                    cell.coord[1])
                if interactibles:
                    if cell.unit is None:
                        self.treat_click_destination(cell)
                    else:
                        choices = self.get_interaction_choices(interactibles)
                        if choices:
                            self.user_make_choice(choices)
                else:
                    self.treat_click_destination(cell)
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
        if self.selected_unit:
##            cell = self.me.cam.get_cell(e.pos)
##            assert cell is self.cell_under_cursor
            cell = self.cell_under_cursor
            if cell:
                print("treat interaction RMB")
                interactibles = self.game.get_interactive_objects( cell.coord[0],
                                                                    cell.coord[1])
                choices = self.get_interaction_choices(interactibles)
                if choices:
                    self.user_make_choice(choices)
                else:
                    return
        self.destinations_mousemotion = []
        self.destinations_lmb = []
        self.selected_unit = None

    def mousemotion(self, e):
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            self.cell_under_cursor = cell
            if self.destinations_lmb: #then the user may be tracing the path
                value = self.last_destination_score.get(cell.coord, None)
                if value:
                    cost, path = value
                    for coord in path:
                        rect = self.me.cam.get_rect_at_coord(coord)
                        self.destinations_mousemotion.append(rect.center)
            else:
                self.destinations_mousemotion = self.get_destinations(cell)
        else:
            self.cell_under_cursor = None

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
                text = self.font_life.render(str(u.quantity), True, self.life_font_color)
                x,y = self.game.me.cam.get_rect_at_coord(u.cell.coord).center
                coord = x+4,y+4
                self.lifes.append((text, coord))

    def unit_under_cursor(self):
        if self.cell_under_cursor:
            return self.cell_under_cursor.unit
        else:
            return None

    def draw_before_objects(self, s):
        self.enhancer.draw_footprints()
        self.refresh_moving_units()
        uuc = self.unit_under_cursor()
        if uuc:
            self.draw_highlight(uuc, "yellow", s)
        if self.selected_unit:
            if self.selected_unit is not uuc:
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
        reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, self.rmb,{"button":3})
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

    def show_options(self):
        e_life_size = thorpy.SliderX(100, (6, 20), "Life font size", type_=int,
                                            initial_value=self.life_font_size)
        e_life_color = thorpy.ColorSetter(text="Life font color",
                                            value=self.life_font_color)
        e_title = thorpy.make_text("Units life")
        e_box = thorpy.make_ok_cancel_box([e_title, e_life_size, e_life_color])
        e_box.center()
        result = thorpy.launch_blocking(e_box)
        print("RESULT",result.how_exited)
        if result.how_exited == "done":
            self.life_font_size = e_life_size.get_value()
            self.life_font_color = e_life_color.get_value()
            self.refresh_graphics_options()



def get_help_box():
    return elements.HelpBox([
        ("Move camera",
            [("To move the map, drag it with", "<LMB>",
                "or hold", "<LEFT SHIFT>", "while moving mouse."),
             ("The minimap on the upper right can be clicked or hold with",
                "<LMB>", "in order to move the camera."),
             ("The","<KEYBOARD ARROWS>",
              "can also be used to scroll the map view.")]),

        ("Zoom",
            [("Use the","zoom slider","or","<NUMPAD +/- >",
              "to change zoom level."),
             ("You can also alternate zoom levels by pressing","<RMB>",".")]),

        ("Miscellaneous",
            [("Press","<G>","to toggle grid lines display."),
             ("Press", "<L>", "to toggle the display of units life.")])
        ])
