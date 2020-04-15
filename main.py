"""
Fantasy Strategia - A 2D, turn-based strategy game in a fantasy universe.
(C) Yann Thorimbert - 2020
yann.thorimbert@gmail.com
"""
from __future__ import print_function, division

import dependenciescheck as dc
dc.check_console("thorpy")
dc.check_gui("numpy")
dc.check_gui("PIL")

import pygame
import thorpy #for GUI and other graphics - see www.thorpy.org

import maps.maps as maps
import gui.gui as gui
from logic.races import Race, LUNAR, STELLAR, SOLAR
from logic.game import Game, get_sprite_frames
import gui.theme as theme
from logic.player import Player
################################################################################

theme.set_theme("human")

W,H = 1200, 700 #screen size
FPS = 60
app = thorpy.Application((W,H))

map_initializer = maps.map1 #go in mymaps.py and PLAY with PARAMS !!!
map_initializer.chunk = (1322, 43944)
map_initializer.max_number_of_roads = 5 #5
map_initializer.max_number_of_rivers = 5 #5
map_initializer.village_homogeneity = 0.1
map_initializer.seed_static_objects = 15

##map_initializer.chunk = (11,9)
##map_initializer.reverse_hmap = False
me = map_initializer.configure_map_editor(FPS) #me = "Map Editor"
game = Game(me)


################################################################################
############################ OBJECTIF IMMEDIAT #################################
################################################################################

#si gui.current_simulation, remplacer si pas le meme unit !!!


##toujours possible d'annuler un deplacement si rien d'autre n'a ete fait depuis
#avant bataille, laisser le temps de voir les troupes avant que commencent a courir

#draw_actions_poss n'a pas besoin d'etre appele sur TOUTES units sauf is building

#sons: cris de guerre. SoundSnap, acheter quand meme ?
#penser a enlever check integrity dans func time
#update loading bar
#ajouter 2 musiques

################################################################################
#Valider le jeu sur 3 types d'units : fermier, fantassin, mage
#conquete de base et batailles. Pas d'impots ni de gestion hors production unites.
#village peuvent etre conquis et ***peuvent produire unites***
# ***ressources : or, population***
##==> a quoi sert-il de planter des drapeaux, d'ailleurs ? : a conquerir villages.
##==> ***Tous les villages ont des drapeaux***
#Ressources ??? : or.

#2. FEUX:
    #attention : bruler est une action a part entiere, empeche d'attaquer dans le meme tour

#3. VILLAGES:
    #Comment produisent-ils des unites ? (clique droit)

#4. SYSTEME DE JEU ET REGLES:
    #avant bataille, indiquer les bonus de defense et d'attaque, et autres aides de prevision

#fusionner les thorpy ICI et git!!!!

#TEST !! - V a1

#load/save
#editeur terrain

#TEST - V a2

#puis suite...


################################################################################
################################################################################
################################################################################

#plain_star a plusieurs frames.

#refaire thorpy avec le seul changement que on enleve tous les pygame.update. C'est l'utilisateur qui fait un flip.
#et il n'y a pas de unblit. On reblit tout chaque frame.

#virer InteractiveObject : ne sert a rien !!! (cf windmills)
#==> remove_from_game devient remove_unit_from_game

#remettre l'altitude, et compte dans bataille ! Mais pas l'altitude par cell : juste l'altitude correspondant au material, sinon pas assez lisible au niveau gameplay

#archers en priorite !!! (implique d'attacher fumee et sons aux classes de projectils)

#faire unite = joueur = stratege/general sur un cheval

##Mettre des monuments (objets comme drapeaux mais avec image differente) qui augmentent le prestige(rayonnement).
## rayonnement = somme( 1. / distance à capitale ennemie de chaque monument). Les monuments coutent cher et sont construits par villageois/ouvriers?.

#Population~nourriture, or~population*impots, rayonnement~monuments, crainte/respect~choix (viols etc)
#couper bois ? ressourece bois, avec camp de bucherons ?

#barre de choix d'impots : (c = curseur)
##Low tax, raise people popularity <------c----------------> High tax, lower people popularity

#pour augmenter le respect, il faut soi-même participer aux batailles de temps a autres
#2 popularites : celle du peuple (people popularity) et celle de l'armee (army popularity)
# case a cocher : allow rapes, allow pillages, ==> curseur entre celle du peuple et de l'armee

#au final, la popularite totale (armee + people) determine:
##    *les rebellions spontanees (villages soudain neutres)
##    *si on peut debloquer certains unites/fonctions/ameliorations

#murailles: au niveau de l'implementation, sont des types d'unites! (static unit)
#       Les chateaux sont juste des villages entoures de murailles
#dans l'editeur, set_material fera en realite un set_height !

#rappel : il n'y a pas de haches/epees/lances etc ; c'est la race qui change ca dans sa propre infanterie !!!

#certaines unites ne sont produites que dans les donjons : (arch)wizards, kings, ...

#impots, incendie, viols ==> depend de ce qu'on cherche a avoir, de la popularite
#       aupres de ses soldats deja existants ou bien des futurs ressortissants des villes prises
#3 scores : score militaire, score moral, score economique

#chateaux : villages/donjons entoures de murailles, avec armes de jet a l'interieur


################################################################################






humans = Race("Green team", "human", LUNAR, me, "green", team=1) #LUNAR, STELLAR or SOLAR
humans.base_material_cost["grass"] = 2
humans.base_material_cost["forest"] = 5
humans.dist_factor = 10
##humans.base_terrain_attack["grass"] = 2.
humans["infantry"].material_cost["sand"] = 4
humans["infantry"].terrain_attack["snow"] = 0.8
humans.finalize() #always call this function to finish initialize a race !!!

humans2 = Race("Red team", "human", SOLAR, me, "red", team=2)
humans2.base_material_cost["forest"] = 10
##humans2.base_terrain_attack["grass"] = 0.8
humans2.dist_factor = 10
humans2.finalize()

players = [ Player(1, "Helmut", humans),
            Player(2, "Jean", humans2)]
game.set_players(players)

#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower. Req. Numpy!
#<load_tilers> : Very slow but needed if you don't have Numpy but still want hi quality.
game.build_map(map_initializer, fast=False, use_beach_tiler=True, load_tilers=False)

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
game.add_unit((14,1), humans["villager"], 10)
game.add_unit((12,11), humans2["wizard"], 30)
game.add_unit((17,3), humans["villager"], 10)

game.add_unit((18,7), humans2["infantry"], 10)
game.add_unit((18,8), humans["infantry"], 10)
game.add_unit((17,10), humans["wizard"], 10)
game.add_unit((16,9), humans2["villager"], 15)
game.add_unit((15,9), humans2["infantry"], 15)

game.add_unit((22,2), humans["infantry"], 10)
game.add_unit((23,2), humans2["infantry"], 20)
game.add_unit((23,4), humans["wizard"], 1)

game.add_unit((20,10), humans2["infantry"], 10)
game.add_unit((20,11), humans["infantry"], 10)

game.add_unit((24,19), humans2["infantry"], 10)
game.add_unit((25,19), humans["infantry"], 10)
game.add_unit((23,20), humans["infantry"], 10)
game.add_unit((24,20), humans2["infantry"], 10)

game.add_unit((12,4), humans["infantry"], 10)
game.add_unit((13,4), humans2["infantry"], 10)

game.add_unit((23,12), humans2["infantry"], 10)

game.add_object((18,10),game.windmill)


game.set_flag((18,5), humans.flag, humans.team)

##game.set_flag((15,7), humans.flag, 1)
##game.set_fire((15,7), 2)
##game.add_smoke("small", (8,8))
##game.add_smoke("large", (10,8))

##game.get_cell_at(15,14).set_name("My top cell")

#### GUI and events part #######################################################


ui = gui.Gui(game)
game.set_ambiant_sounds(False)

thorpy.add_time_reaction(me.e_box, game.func_reac_time)

game.gui.footstep = get_sprite_frames("sprites/footstep.png", s=12,
                                        resize_factor=0.6)
game.gui.sword = get_sprite_frames("sprites/sword_shine.png")
game.gui.medic = get_sprite_frames("sprites/medic.png", s=16)
game.gui.under_construct = get_sprite_frames("sprites/under_construction.png", s=16)
game.gui.under_capture = get_sprite_frames("sprites/under_capture.png", s=16)

game.update_player_income(game.current_player)
game.gui.e_gold_txt.set_text(str(game.current_player.money))
game.gui.empty_star = get_sprite_frames("sprites/star_empty.png", s=13)[0]
game.gui.plain_star = get_sprite_frames("sprites/star_plain.png", s=13)[0]

#me.e_box includes many default reactions. You can remove them as follow:
#remove <g> key:
##me.e_box.remove_reaction("toggle grid")
#remove arrows keys, replacing <direction> by left, right, up or down:
##me.e_box.remove_reaction("k <direction>")
#remove +/- numpad keys for zoom, replacing <sign> by plus or minus:
##me.e_box.remove_reaction("k <sign>")
#remember to modify/deactivate the help text corresponding to the removed reac

##game.me.lm.frame_slowness = 30
game.check_integrity()
me.set_zoom(level=0)
##thorpy.application.SHOW_FPS = True
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

##neige et pluie comme dans torus, et tangage bateau

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

#utiliser la methode blits de pygame1.9 de surface et comparer perf (test : bataille)!
