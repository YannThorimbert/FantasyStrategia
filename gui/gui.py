import pygame, thorpy, math
from pygame.math import Vector2 as V2
import PyWorld2D.gui.elements as elements
import PyWorld2D.gui.parameters as guip
import PyWorld2D.saveload.io as io
from FantasyStrategia.logic.battle import Battle, DistantBattle
from FantasyStrategia.logic.game import INCOME_PER_VILLAGE

def quit_func():
    io.ask_save(me)
    thorpy.functions.quit_func()

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

    def __init__(self, game, time_remaining=-1):
        self.game = game
        game.gui = self
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
        self.forced_gotocell = False
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
        self.e_cant_move = guip.get_infoalert_text("Can't go there")
        self.e_cant_move_another = guip.get_infoalert_text("Another unit is already going there")
        self.e_wrong_team = guip.get_infoalert_text("You cannot command another player's units")
        self.e_already_moved = guip.get_infoalert_text("This unit has already moved in this turn")
        #
        self.moving_units = []
        self.add_reactions()
        self.life_font_size = guip.NFS
        self.life_font_color = (0,0,0)
        self.font_life = pygame.font.SysFont(guip.font_gui_life, self.life_font_size)
        self.refresh_lifes()
        self.show_lifes = True
        self.actions = {"flag":[("Remove flag",self.remove_selected_flag,
                                    self.check_interact_flag),
                                ("Replace flag",self.set_flag_on_cell_under_cursor,
                                    self.check_replace_flag)],
                        "fire":[("Extinguish",self.extinguish,
                                    self.check_extinguish)]
                        }
        self.actions_no_objs = [("Plant flag",self.set_flag_on_cell_under_cursor,
                                    self.check_plant_flag),
                                ("Burn",self.burn,
                                    self.check_interact_burn)]
##                                ("Go there",self.choice_gotocell,
##                                    self.check_interact_gotocell)]
        self.interaction_objs = []
        #
        #here you can add/remove buttons to/from the menu
        e_options = thorpy.make_button("Options", self.show_options)
        e_save = thorpy.make_button("Save", io.ask_save, {"me":self.me})
        e_load = thorpy.make_button("Load", io.ask_load)
        e_quit = thorpy.make_button("Quit game", quit_func)
        self.menu = thorpy.make_ok_box([ get_help_box().launcher,
                                                    e_options,
                                                    e_save,
                                                    e_load,
                                                    e_quit])
        self.menu.center()
        self.set_map_gui()
        self.has_moved = []
        self.footstep = None
        self.sword = None
        self.medic = None
        self.can_be_fought = []
        self.can_be_helped = []

    def set_map_gui(self):
        me = self.me
        ########################################################################
        self.hline = thorpy.Line(int(0.75*me.e_box.get_fus_rect().width), "h")
        me.add_gui_element(self.hline, True)
        ########################################################################
        self.e_end_turn = thorpy.make_button("End turn", self.game.end_turn)
        self.e_end_turn.set_font_size(int(1.2*guip.TFS))
        self.e_end_turn.set_font_color(guip.TFC)
        self.e_end_turn.scale_to_title()
        w,h = self.e_end_turn.get_fus_size()
        self.e_end_turn.set_size((w,int(0.75*w)))
##        nothing = thorpy.make_text("",20)
##        self.e_end_turn = thorpy.make_group([e_end_turn, nothing], "v")
        me.add_gui_element(self.e_end_turn, True)
        ########################################################################
        me.add_gui_element(self.hline.copy(), True)
        ########################################################################
        self.e_show_players = thorpy.make_button("More statistics",
                                                 self.show_players_infos)
        me.add_gui_element(self.e_show_players, True)
        ########################################################################
        n = self.game.count_villages(self.game.current_player.team)
        self.e_pop_txt = thorpy.make_text(str(n))
        img = pygame.image.load("sprites/house.png")
        img = pygame.transform.scale(img, (32,32))
        self.e_pop_img = thorpy.Image(img, colorkey=(255,255,255))
        self.e_pop = thorpy.make_group([self.e_pop_img, self.e_pop_txt])
        me.add_gui_element(self.e_pop, True)
        ########################################################################
        self.e_gold_txt = thorpy.make_text(str(self.game.current_player.money))
        self.e_gold_img = thorpy.Image("sprites/coin1.png",
                                        colorkey=(255,255,255))
        self.e_gold = thorpy.make_group([self.e_gold_img, self.e_gold_txt])
        me.add_gui_element(self.e_gold, True)
        ########################################################################
        me.add_gui_element(self.hline.copy(), True)
        ########################################################################
        text_day = self.get_day_text()
        if text_day:
            self.e_time_remaining = guip.get_highlight_text(text_day)
            me.add_gui_element(self.e_time_remaining, True)
        ########################################################################
        self.e_info_day = guip.get_title("Day "+str(self.game.days_elapsed))
        me.add_gui_element(self.e_info_day, True)
        ########################################################################
        me.add_gui_element(self.hline.copy(), True)
        self.e_info_player = guip.get_title(self.game.current_player.name)
        self.e_info_player.set_font_color(self.game.current_player.color_rgb)
        me.add_gui_element(self.e_info_player, True)
        ########################################################################
        me.menu_button.user_func = self.launch_map_menu


    def show_players_infos(self):
        ...

    def get_day_text(self):
        if self.game.days_left > 0:
            if self.game.days_left == 1:
                return "Last day !"
            else:
                return str(self.game.days_left) + " days left"

    def extinguish(self):
        for o in self.cell_under_cursor.objects:
            if o.str_type == "fire":
                self.game.extinguish(self.cell_under_cursor.coord)

    def check_extinguish(self):
        u = self.selected_unit
        if u.cell.distance_to(self.cell_under_cursor) <= u.help_range[1]:
            n = u.str_type
            return n == "wizard" or n == "arch_wizard"
        return False

    def launch_map_menu(self):
        thorpy.launch_blocking(self.menu)

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
                if o.str_type in self.game.is_burnable:
                    return True
            for o in self.cell_under_cursor.objects:
                if o.str_type == "river":
                    return False
        return self.cell_under_cursor.material.name.lower() in self.game.is_burnable


    def check_interact_flag(self):
        c = self.cell_under_cursor
        if c.coord != self.selected_unit.cell.coord:
            return False
        if self.game.burning.get(c.coord):
            return False
        if c.unit:
            if c.unit.team != self.selected_unit.team:
                return False
##        if self.selected_unit.cell.distance_to(c) <= 1:
        for o in c.objects:
            if o.str_type == "river":
                return False
        return c.material.name.lower() in self.game.is_flaggable

    def check_plant_flag(self):
##        for o in self.interaction_objs:
        for o in self.cell_under_cursor.objects:
            if o.str_type == "flag":
                return False
        return self.check_interact_flag()

    def check_replace_flag(self):
        if self.check_interact_flag():
##            for o in self.interaction_objs:
            for o in self.cell_under_cursor.objects:
                if o.str_type == "flag":
                    print(o.team, self.selected_unit.team)
                    return o.team != self.selected_unit.team

    def check_interact_gotocell(self):
        c = self.cell_under_cursor
        if self.game.burning.get(c.coord):
            return False
        if c.unit:
            return False
        rect = self.me.cam.get_rect_at_coord(c.coord)
        if rect.center in self.destinations_lmb:
            return True

    def choice_gotocell(self):
        self.forced_gotocell = True

    def clear(self):
        print("CLEAR")
        self.selected_unit = None
        self.cell_under_cursor = None
        self.blue_highlights = []
        self.red_highlights = []
        self.interaction_objs = []
        self.can_be_fought = []
        self.can_be_helped = []

    def get_destinations(self, cell):
        destinations = []
        self.red_highlights = []
        self.blue_highlights = []
        self.can_be_fought = []
        self.can_be_helped = []
        if cell.unit:
            if cell.unit.anim_path: #moving unit, let it alone...
                return []
            elif cell.unit in self.has_moved:
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

    def update_possible_help_and_fight(self, coord):
        ref_unit = self.selected_unit
        if not ref_unit:
            ref_unit = self.cell_under_cursor
        for other in self.game.units:
            if other is not ref_unit:
                d = other.cell.distance_to_coord(coord)
                if other.team == ref_unit.team:
                    if d <= ref_unit.help_range[1]:
                        self.can_be_helped.append(other)
                elif d <= ref_unit.attack_range[1]:
                    self.can_be_fought.append(other)

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
            self.has_moved.append(u)


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
##                    #check that same type and sum of quantities does not exceed max_quantity
##                    u1 = self.selected_unit
##                    u2 = friend
##                    MAX_QUANTITY = 20
##                    ok = u2.str_type == u1.str_type and u1.quantity + u2.quantity <= MAX_QUANTITY
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
        if self.selected_unit.quantity > 0:
            self.selected_unit.make_grayed()
        self.clear()
        thorpy.get_current_menu().fps = guip.FPS
        self.refresh_lifes()

    def distant_attack(self):
        defender = self.unit_under_cursor()
        distance = defender.distance_to(self.selected_unit)
        units_in_battle = [self.selected_unit, defender]
        b = DistantBattle(self.game, units_in_battle, defender, distance)
        b.fight()
        if self.selected_unit.quantity > 0:
            self.selected_unit.make_grayed()
        self.clear()
        thorpy.get_current_menu().fps = guip.FPS
        self.refresh_lifes()

    def remove_selected_flag(self):
        for o in self.interaction_objs:
            if o.str_type == "flag":
                o.remove_from_game()
                break
        #
        self.selected_unit.make_grayed()
        #
        self.game.refresh_village_gui()

    def set_flag_on_cell_under_cursor(self):
        self.remove_selected_flag()
        self.game.set_flag(self.cell_under_cursor.coord,
                            self.selected_unit.race.flag,
                            self.selected_unit.team,
                            sound=True)
        self.game.refresh_village_gui()

    def burn(self):
        self.game.set_fire(self.cell_under_cursor.coord, 4)
        self.selected_unit.make_grayed()

    def help(self):
        friend = self.unit_under_cursor()
        self.selected_unit.make_grayed()
        print("helping", friend.name, friend.team == self.selected_unit.team)
##        raise Exception("Not implemented yet")

    def get_interaction_choices(self, objs, exceptions=""):
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
                    if d > 1 and self.selected_unit.help_range[1] >= d: #distant help
                        choices["Distant help"] = self.help
                    elif d == 1:
                        choices["Help"] = self.help
            for o in objs:
                if o != cell.unit:
                    if o.str_type in self.actions:
                        for name, func, check in self.actions[o.str_type]:
                            if name in exceptions:
                                continue
                            if check():
                                choices[name] = func
            self.interaction_objs = objs
        for name, func, check in self.actions_no_objs:
            if name in exceptions:
                continue
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
        if not self.forced_gotocell:
            self.clear()



    def lmb_unit_already_moved(self, cell):
        if self.selected_unit.is_grayed:
            self.clear()
        else:
            self.update_possible_help_and_fight(self.selected_unit.cell.coord)
            if cell.unit in self.can_be_fought:
                d = cell.distance_to(self.selected_unit.cell)
                if d > 1:
                    self.distant_attack()
                else:
                    self.attack()
                self.clear()
            elif cell.unit in self.can_be_helped:
                self.help()
                self.clear()
            else:
                self.rmb(None)
            self.can_be_fought = []
            self.can_be_helped = []


    def lmb(self, e):
        print("LMB", self.game.t, self.selected_unit)
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            if self.destinations_lmb: #user may be clicking a destination
                interactibles = self.game.get_interactive_objects(cell.coord[0],
                                                                  cell.coord[1])
                if interactibles: #there are objects interactibles at the dest.
                    if cell.unit is None:
                        choices = self.get_interaction_choices(interactibles,
                                                    exceptions=["Burn"])
                        if choices:
                            self.user_make_choice(choices)
                        if self.selected_unit:
                            self.treat_click_destination(cell)
                    else: #there is already a unit in the destination
                        choices = self.get_interaction_choices(interactibles,
                                                    exceptions=["Burn"])
                        if choices:
                            self.user_make_choice(choices)
                else:
                    self.treat_click_destination(cell)
                self.destinations_lmb = [] #clear destinations
                self.red_highlights = []
                self.blue_highlights = []
                self.can_be_fought = []
                self.can_be_helped = []
                self.selected_unit = None
            else:#no path (destination) is drawn for lmb
                if self.selected_unit:
                    self.lmb_unit_already_moved(cell)
                if cell.unit:
                    if cell.unit.team == self.game.current_player.team:
                        self.selected_unit = cell.unit
                        if cell.unit in self.has_moved:
                            self.update_possible_help_and_fight(self.selected_unit.cell.coord)
                        else:
                            print("update destinations")
                            self.destinations_lmb = self.get_destinations(cell)
                    else:
                        self.add_alert(self.e_wrong_team)
                        self.game.deny_sound.play()
                else:
                    for o in cell.objects:
                        if o.name == "village":
                            for o2 in cell.objects:
                                if o2.str_type == "flag":
                                    if o2.team == self.game.current_player.team:
                                        self.production(o)
                                        self.selected_unit = None
                                        return
                    self.selected_unit = None


    def rmb(self, e):
        if self.selected_unit:
            cell = self.cell_under_cursor
            if cell:
                print("treat interaction RMB")
                interactibles = self.game.get_interactive_objects(cell.coord[0],
                                                                  cell.coord[1])
                choices = self.get_interaction_choices(interactibles)
                if choices:
                    self.user_make_choice(choices)
                    if self.forced_gotocell:
                        self.forced_gotocell = False
                        self.treat_click_destination(cell)
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
                    self.can_be_fought = []
                    self.can_be_helped = []
                    cost, path = value
                    for coord in path:
                        rect = self.me.cam.get_rect_at_coord(coord)
                        self.destinations_mousemotion.append(rect.center)
                    self.update_possible_help_and_fight(path[-1])
            else:
                if self.selected_unit:
                    self.update_possible_help_and_fight(self.selected_unit.cell.coord)
                else:
##                    for o in cell.objects:
##                        if o.name == "village":
##                            return
                    self.destinations_mousemotion = self.get_destinations(cell)
        else:
            self.cell_under_cursor = None

    def production(self, o):
        from FantasyStrategia.logic.races import std_cost, std_number
        e_title = guip.get_title("Recruitment")
        e_line = thorpy.Line(500, "h")
        choices = []
        race = self.game.get_race_of_player(self.game.current_player)
        def produce_unit(type_):
            self.game.coin_sound.play()
            u = self.game.add_unit(o.cell.coord, race[type_], std_number[type_])
            self.selected_unit.make_grayed()
            self.game.current_player.money -= u.cost * INCOME_PER_VILLAGE
            self.e_gold_txt.set_text(str(self.game.current_player.money))
            self.refresh()
            thorpy.functions.quit_menu_func()
        for unit_type in std_cost:
            if not "boat" in unit_type and not "king" in unit_type:
                if unit_type in race.unit_types:
                    text = str(std_number[unit_type]) + " " + unit_type.capitalize()
                    cost = std_cost[unit_type] * INCOME_PER_VILLAGE
                    grayed = cost > self.game.current_player.money
                    cost = str(cost) + " $"
                    e_text = thorpy.OneLineText(text + "    (" + cost+")")
                    img = race.unit_types[unit_type].imgs_z_t[0][0]
                    e_img = thorpy.Image(img)
                    e_ghost = thorpy.make_group([e_img, e_text])
                    if grayed:
                        button = thorpy.Pressable(elements=[e_ghost])
                        button.fit_children()
                        button.active = False
                        button.set_pressed_state()
                    else:
                        button = thorpy.Clickable(elements=[e_ghost])
                        button.fit_children()
                        button.add_basic_help(race.unit_descr[unit_type])
                    button.user_func = produce_unit
                    button.user_params = {"type_":unit_type}
                    choices.append(button)
        def click_outside(event):
            if not e.get_fus_rect().collidepoint(event.pos):
                thorpy.functions.quit_menu_func()
        e = thorpy.make_ok_box([e_title, e_line]+choices)
        e.center()
        reac = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, click_outside)
        e.add_reaction(reac)
        thorpy.launch_blocking(e, add_ok_enter=True)


    def get_alpha_dest(self):
        t = self.me.lm.tot_time
        return math.sin(t * self.dest_omega) * self.dest_alpha_amplitude + self.dest_alpha0

    def draw_highlight(self, unit, color, s):
        img = unit.get_current_highlight(color)
        rect = img.get_rect()
        rect.center = unit.get_current_rect_center(s)
        self.surface.blit(img, rect.topleft)

    def draw_actions_possibility(self, unit, s):
        x,y = unit.get_current_rect_center(s)
        if unit in self.has_moved:
            t = self.game.me.lm.t3 % len(self.footstep)
            self.surface.blit(self.footstep[t], (x-s//2,y))
        if unit in self.can_be_fought:
            t = self.game.me.lm.t % len(self.sword)
            img = self.sword[t]
            rect = img.get_rect()
            rect.center = (x,y)
            self.surface.blit(img, rect)
        elif unit in self.can_be_helped:
            t = self.game.me.lm.t3 % len(self.medic)
            img = self.medic[t]
            rect = img.get_rect()
            rect.center = (x,y)
            self.surface.blit(img, rect)

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
        for u in self.game.units:
            self.draw_actions_possibility(u, s)

    def refresh(self):
        self.enhancer.refresh()
        if self.game.need_refresh_ui_box:
            self.e_info_day.set_text("Day "+str(self.game.days_elapsed))
            if self.game.days_left > 0:
                self.e_time_remaining.set_text(self.get_day_text())
            if self.game.days_left < 3:
                self.e_time_remaining.set_font_color((255,0,0))
            else:
                self.e_time_remaining.set_font_color((0,0,0))
            self.e_info_player.set_font_color(self.game.current_player.color_rgb)
            self.e_info_player.set_text(self.game.current_player.name)
            thorpy.store(self.me.e_box)
            self.game.need_refresh_ui_box = False

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
        shortcuts = [(pygame.K_l, self.toggle_show_life),
                     (pygame.K_ESCAPE, self.launch_map_menu)]
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
        self.me.draw()
        self.menu.blit()
        pygame.display.flip()


    def show_animation_income(self, from_, to, fps=60):
        game = self.game
        COIN_PER_VILLAGE = 3
        MOD_SPAWN = 10
        MAX_VEL = 10
        STOP_DIST = 10
        p = game.current_player
        img = self.e_gold_img.get_image()
        sources = {}
        target = self.e_gold_img.get_fus_rect().topleft
        for f in game.get_all_objects_by_str_type("flag"):
            if f.team == p.team:
                for o in f.cell.objects:
                    if o.name == "village":
                        sources[o.cell.coord] = 0
                    break
        delta_coin = int((to - from_) / (COIN_PER_VILLAGE * len(sources)))
        print(game.current_player.name, "FROM", from_, "TO", to, "DELTA", delta_coin)
        coins_flying = []
        done = False
        clock = pygame.time.Clock()
        i_anim = 0
        money = from_
        self.e_gold_txt.set_text(str(money))
        while not done:
            self.refresh()
            game.me.func_reac_time()
            clock.tick(fps)
            if i_anim%MOD_SPAWN == 0:
                for src in sources:
                    if sources[src] < COIN_PER_VILLAGE:
                        cam_coord = game.me.cam.get_rect_at_coord(src).topleft
                        coins_flying.append(cam_coord)
                        sources[src] += 1
            new_coins_flying = []
            for x,y in coins_flying:
                game.me.screen.blit(img, (x,y))
                delta = V2(target) - (x,y)
                L = delta.length()
                if L > MAX_VEL:
                    delta.scale_to_length(MAX_VEL)
                if L > STOP_DIST:
                    x += delta.x
                    y += delta.y
                    new_coins_flying.append((x,y))
                else:
                    money += delta_coin
                    game.coin_sound.play_next_channel()
                    self.e_gold_txt.set_text(str(money))
            coins_flying = new_coins_flying
            pygame.display.flip()
            i_anim += 1
            if not coins_flying:
                done = True



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
