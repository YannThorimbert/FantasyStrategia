"""
Fantasy Strategia - A 2D, turn-based strategy game in a fantasy universe.
Yann Thorimbert - 2019
yann.thorimbert@gmail.com
"""
from __future__ import print_function, division

import dependenciescheck as dc
dc.check_console("thorpy")
dc.check_gui("numpy")
dc.check_gui("PIL")

import pygame
import thorpy #for GUI and other graphics - see www.thorpy.org


from PyWorld2D import PW_PATH
from PyWorld2D.mapobjects.objects import MapObject
import PyWorld2D.saveload.io as io
from PyWorld2D.editor.mapeditor import MapEditor #base structure for a map
from PyWorld2D.editor.mapbuilding import MapInitializer #configuration structure of a map

import maps.maps as maps
import gui.gui as gui
from logic.unit import Unit, InteractiveObject
##from logic.interactiveobject import InteractiveObject
from logic.races import Race, LUNAR, STELLAR, SOLAR
from logic.game import Game
import gui.theme as theme

theme.set_theme()

W,H = 1200, 700 #screen size
app = thorpy.Application((W,H))

map_initializer = maps.map1 #go in mymaps.py and PLAY with PARAMS !!!
me = map_initializer.configure_map_editor() #me = "Map Editor"
game = Game(me)

################################################################################
######################## OBJECTIF IMMEDIAT #####################################
################################################################################
#Finir tous les sprites relatifs aux batailles
#Valider le jeu sur 3 types d'units : fermier, fantassin, mage
#conquete de base, batailles. Pas d'impots ni de destruction d'objets.

#objets du jeu (eg drapeaux pour les maisons, maisons construites/detruites).
comment faire qu'une unite se deplace sur case d'un drapeau ? Soit click droit pour interagir, soit "go there" dans les actions
nom du flag contient race et team ?



#mettre foret dans le layer des villages, peut-être pas si mal

################################################################################
################################################################################
################################################################################

#meilleur wood : taper wood texture pixel art sur google. Wooden planks?

#murailles: au niveau de l'implementation, sont des types d'unites! (static unit)
#       Les chateaux sont juste des villages entoures de murailles
#dans l'editeur, set_material fera en realite un set_height !

#rappel : il n'y a pas de haches/epees/lances etc ; c'est la race qui change ca dans sa propre infanterie !!!

#sons: cris de guerre. SoundSnap, acheter quand meme ?

#tester !!!

#impots, incendie, viols ==> depend de ce qu'on cherche a avoir, de la popularite
#       aupres de ses soldats deja existants ou bien des futurs ressortissants des villes prises
#3 scores : score militaire, score moral, score economique

#chateaux : villages entoures de murailles, avec armes de jet a l'interieur


################################################################################
#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower. Req. Numpy!
#<load_tilers> : Very slow but needed if you don't have Numpy but still want hi quality.
map_initializer.build_map(me, fast=False, use_beach_tiler=False, load_tilers=False)
##map_initializer.build_map(me, fast=False, use_beach_tiler=False, load_tilers=False)


humans = Race("Green team", "human", LUNAR, me, "green", team=1)
humans.base_material_cost["grass"] = 2
humans.base_material_cost["forest"] = 5
humans.dist_factor = 10
##humans.base_terrain_attack["grass"] = 2.
humans["infantry"].material_cost["sand"] = 4
humans["infantry"].terrain_attack["snow"] = 0.8
humans.finalize() #always call this function to finish initialize a race !!!

humans2 = Race("White team", "human", SOLAR, me, "red", team=2)
humans2.base_material_cost["forest"] = 10
##humans2.base_terrain_attack["grass"] = 0.8
humans2["wizard"].material_cost["wood"] = 2.
humans2.dist_factor = 10
humans2.finalize()

##game.add_unit((15,5), humans["infantry"], 100, team=1)
##game.add_unit((14,6), humans["infantry"], 100, team=1) #14,6
##game.add_unit((25,5), humans["infantry"], 100, team=1)
##game.add_unit((16,6), humans["wizard"], 1, team=1)
##
##
##game.add_unit((20,8), humans2["infantry"], 100, team=2)
##game.add_unit((15,7), humans2["infantry"], 100, team=2)

game.add_unit((14,10), humans2["wizard"], 10)
game.add_unit((14,9), humans["infantry"], 10)
game.add_unit((15,10), humans2["infantry"], 10)
game.add_unit((13,10), humans["wizard"], 30)
game.add_unit((14,1), humans["infantry"], 10)
game.add_unit((12,11), humans2["wizard"], 30)

game.add_unit((18,8), humans["infantry"], 1)
game.add_unit((17,10), humans["wizard"], 1)
game.add_unit((16,9), humans2["villager"], 15)
game.add_unit((15,9), humans2["infantry"], 15)



##flag = InteractiveObject("flag", me, "sprites/flag", race=humans2)
game.add_object((15,11), humans2.flag, 1)
##game.add_fire(15,15)


##game.get_cell_at(14,15).set_name("My left cell")
##game.get_cell_at(15,14).set_name("My top cell")

#### GUI and events part #######################################################

ui = gui.Gui(game)
game.outdoor_sound.play(-1)

def func_reac_time(): #here add wathever you want
    """Function called each frame"""
    ui.refresh()
    me.func_reac_time()
    game.t += 1
    pygame.display.flip()
thorpy.add_time_reaction(me.e_box, func_reac_time)


#here you can add/remove buttons to/from the menu
def quit_func():
    io.ask_save(me)
    thorpy.functions.quit_func()
e_quit = thorpy.make_button("Quit game", quit_func)
e_save = thorpy.make_button("Save", io.ask_save, {"me":me})
e_load = thorpy.make_button("Load", io.ask_load)

launched_menu = thorpy.make_ok_box([ me.help_box.launcher,
                                            e_save,
                                            e_load,
                                            e_quit])
launched_menu.center()
me.menu_button.user_func = thorpy.launch_blocking
me.menu_button.user_params = {"element":launched_menu}

#me.e_box includes many default reactions. You can remove them as follow:
#remove <g> key:
##me.e_box.remove_reaction("toggle grid")
#remove arrows keys, replacing <direction> by left, right, up or down:
##me.e_box.remove_reaction("k <direction>")
#remove +/- numpad keys for zoom, replacing <sign> by plus or minus:
##me.e_box.remove_reaction("k <sign>")
#remember to modify/deactivate the help text corresponding to the removed reac

##reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, ui.lmb,{"button":1})
##me.e_box.add_reaction(reac_click)
##reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, ui.rmb,{"button":2})
##me.e_box.add_reaction(reac_click)
##reac_motion = thorpy.Reaction(pygame.MOUSEMOTION, ui.mousemotion)
##me.e_box.add_reaction(reac_motion)


print("0,0 ======= ", game.get_cell_at(0,0).h)

me.set_zoom(level=0)
m = thorpy.Menu(me.e_box,fps=me.fps)
##game.outdoor_sound.play(-1)
m.play()

app.quit()

##Below is shown how to get a path, if you need it for an IA for instance:
##from ia.path import BranchAndBoundForMap
##costs_materials = {name:1. for name in me.materials}
##costs_materials["Snow"] = 10. #unit is 10 times slower in snow
##costs_materials["Thin snow"] = 2.
##costs_materials["Sand"] = 2.
##costs_objects = {bush.object_type: 2.}
##sp = BranchAndBoundForMap(lm, lm.cells[15][15], lm.cells[8][81],
##                 costs_materials, costs_objects,
##                 possible_materials, possible_objects)
##path = sp.solve()
##draw_path(path, objects=cobbles, layer=lm)



###############################################################################

#*********************************v2:
#editeur ==> sauver les materiaux et heights modifies
#riviere : si mer est trop loin, va a max length puis fait un lac
###quand meme tester sans numpy, parce que bcp de modules l'importent (surfarray)
###tester python2


#nb: l'editeur permet de faire terrain (changer hauteur) (hmap), materials, objects (dyn/statics)
#herbe animee
#ombres des objets en mode pil, y compris dans bataille (si option)
#ridged noise
#effets: fumee villages, ronds dans l'eau, herbe dans pieds, traces dans neige et sable, precipitations
