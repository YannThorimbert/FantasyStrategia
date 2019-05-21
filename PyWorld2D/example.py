"""Yann Thorimbert - 2018
yann.thorimbert@gmail.com
"""
from __future__ import print_function, division
import pygame
import thorpy #for GUI and other graphics - see www.thorpy.org
from mapobjects.objects import MapObject #to create objects to add to a map
import saveload.io as io #handling save/load maps
from editor.mapeditor import MapEditor #base structure for a map
from editor.mapbuilding import MapInitializer #configuration structure of a map
import mymaps #store some pre-defined maps so you can play with

###ne pas oublier d'ajouter thorpy

#IMPORTANT : probably almost all you need is inside mymaps.py, which provides
#examples about map configuration.

#At the end of this file, I provide some ways to do things like use a path finding
#algorithm, etc.

W,H = 800, 600 #screen size
app = thorpy.Application((W,H))

# The 8 following lines are used to determine if you want to load a map
save_filename = ""
title = thorpy.make_text("What do you want ?", font_size=20, font_color=(200,200,200))
load = io.get_saved_files_button("./")
dont_load = thorpy.make_button("Build a new map", func=thorpy.functions.quit_menu_func)
thorpy.store("screen", [title, load, dont_load])
m = thorpy.Menu([title, load, dont_load])
m.play()
save_filename = load.var_text

if not save_filename: #use a map that I've set for you. Go and see how to tune it:
    map_initializer = mymaps.demo_map2 #go in mymaps.py and PLAY with PARAMS !!!
    me = map_initializer.configure_map_editor() #me = "Map Editor"
else:
    savefile = open(save_filename, "rb")
    me = io.from_file_base(savefile)
    map_initializer = me.map_initializer

#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower. Req. Numpy!
#<load_tilers> : Very slow but needed if you don't have Numpy but still want hi quality.
map_initializer.build_map(me, fast=False, use_beach_tiler=True, load_tilers=False)

if save_filename:
    io.from_file_cells(savefile, me)
    io.from_file_units(savefile, me)
    savefile.close()
else:
    #dynamic objects (you cann add them whenever you want):
    character = MapObject(me, "./mapobjects/images/char1.png", "My Unit", factor=1.)
    obj = me.add_unit(coord=(15,15), obj=character, quantity=12)
    obj.name = "My first unit"
    obj = me.add_unit((13,14), obj=character, quantity=1)
    obj.name = "My second unit"
    #this is how we set the name of a cell
    me.lm.get_cell_at(14,15).set_name("My left cell")
    me.lm.get_cell_at(15,14).set_name("My top cell")
    #we can get the objects belonging to a cell:
    #assert me.lm.get_cell_at(15,15).objects[1].name == "My first unit"


#### GUI and events part #######################################################

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
#ombres des objets en mode pil
#ridged noise
#effets: fumee villages, ronds dans l'eau, herbe dans pieds, traces dans neige et sable, precipitations
#
#couples additionnels (ex: shallow_water with all the others...) ajoute au moment de la creation de riviere ?
#comment gerer brulage d'arbres ? Si ca doit changer l'architecture, y penser maintenant...
### ==> reconstruire localement le layer concerne
#quand res + grande, nb de couples peut augmenter! ==> automatiser sur la base des materiaux existants
#info sur material/unit quand on click dessus dans cell/unit_info.em
