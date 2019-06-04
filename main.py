"""Yann Thorimbert - 2019
yann.thorimbert@gmail.com
"""
from __future__ import print_function, division
import pygame
import thorpy #for GUI and other graphics - see www.thorpy.org

from PyWorld2D import PW_PATH
from PyWorld2D.mapobjects.objects import MapObject
import PyWorld2D.saveload.io as io
from PyWorld2D.editor.mapeditor import MapEditor #base structure for a map
from PyWorld2D.editor.mapbuilding import MapInitializer #configuration structure of a map


import maps.maps as maps
import gui.gui as gui
from logic.unit import Unit
from logic.races import Race
from logic.game import Game


W,H = 1200, 700 #screen size
##W,H = 500,500
app = thorpy.Application((W,H))

map_initializer = maps.map1 #go in mymaps.py and PLAY with PARAMS !!!
me = map_initializer.configure_map_editor() #me = "Map Editor"
game = Game(me)


#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower. Req. Numpy!
#<load_tilers> : Very slow but needed if you don't have Numpy but still want hi quality.
##map_initializer.build_map(me, fast=False, use_beach_tiler=True, load_tilers=False)
map_initializer.build_map(me, fast=False, use_beach_tiler=False, load_tilers=False)


humans = Race("Humans 1", me, "green")
humans.base_cost["grass"] = 2
humans.base_cost["forest"] = 5
humans.base_max_dist = 10
humans.add_type("infantry", "sprites/human_warrior")
humans["infantry"].cost["sand"] = 4
humans.add_type("wizard", "sprites/human_wizard")

humans2 = Race("Humans 2", me, "white")
humans2.base_cost["forest"] = 10
humans2.add_type("infantry", "sprites/human_warrior")

# humans.add_type("archer", PW_PATH+"/mapobjects/images/char1.png")
# humans["archer"].max_dist = 6
# humans["archer"].cost["cobblestone"] = 1.5

game.add_unit((20,8), humans2["infantry"], 100, team=1)
game.add_unit((15,7), humans2["infantry"], 100, team=1)

game.add_unit((15,5), humans["infantry"], 100, team=2)
game.add_unit((18,5), humans["infantry"], 100, team=2)
game.add_unit((25,5), humans["infantry"], 100, team=2)


game.add_unit((16,6), humans["wizard"], 1, team=2)





##game.get_cell_at(14,15).set_name("My left cell")
##game.get_cell_at(15,14).set_name("My top cell")


#### GUI and events part #######################################################

ui = gui.Gui(game)

def func_reac_time(): #here add wathever you want
    """Function called each frame"""
    me.func_reac_time()
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

reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, ui.lmb,{"button":1})
me.e_box.add_reaction(reac_click)
reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, ui.rmb,{"button":2})
me.e_box.add_reaction(reac_click)
reac_motion = thorpy.Reaction(pygame.MOUSEMOTION, ui.mousemotion)
me.e_box.add_reaction(reac_motion)

me.set_zoom(level=0)
m = thorpy.Menu(me.e_box,fps=me.fps)
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
#CHAQUE DYNAMIC OBJECT A UN DELTA_FRAME ALEATOIRE, COMME CA PAS TOUS SYNCHRO
#pour FS: ajouter un info box quand on click sur material name, quand on click sur une cellule

#pour fs: chateaux, murailles, units: (herite de objet dynamique)

#pour fs : vu que statics prennet de la place, on considere qu'on est dans un village quand on est pres de lui ?
# ou sinon relpos tres petit...


#

#*********************************v2:
#editeur ==> sauver les materiaux et heights modifies
#riviere : si mer est trop loin, va a max length puis fait un lac
###quand meme tester sans numpy, parce que bcp de modules l'importent (surfarray)
###tester python2
#proposer un ciel + nuages (cf perigeo) au lieu de mer ; le mettre par defaut dans le noir ?

#quand curseur passe au dessus d'un village, ajouter (village) a cote du material dans la description de fenetre de droite

#alert pour click droit sur units quand click gauche sur units, et pour click gauche sur terrain quand click droit sur terrain

#meilleur wood : taper wood texture pixel art sur google. Wooden planks?
#nb: l'editeur permet de faire terrain (changer hauteur) (hmap), materials, objects (dyn/statics)
#herbe animee
#ombres des objets en mode pil, y compris dans bataille (si option)
#ridged noise
#effets: fumee villages, ronds dans l'eau, herbe dans pieds, traces dans neige et sable, precipitations
#
#couples additionnels (ex: shallow_water with all the others...) ajoute au moment de la creation de riviere ?
#comment gerer brulage d'arbres ? Si ca doit changer l'architecture, y penser maintenant...
### ==> reconstruire localement le layer concerne
#quand res + grande, nb de couples peut augmenter! ==> automatiser sur la base des materiaux existants
#info sur material/unit quand on click dessus dans cell/unit_info.em
