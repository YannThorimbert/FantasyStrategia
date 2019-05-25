from PyWorld2D.editor.mapbuilding import MapInitializer, terrain_plains, terrain_flat
from PyWorld2D.thornoise.purepython.noisegen import colorscale_plains, colorscale_flat

#Here I simply define some properties of differnt maps. No programmation, just
#configuration.

#For a description of each parameter, please go the file PyWorld2D/editor/mapbuilding.py
#and have a look at the MapInitializer constructor

map0 = MapInitializer("Map0")
map0.chunk = (1400,0)
map0.world_size = (16,16)
##map0.set_terrain_type(terrain_flat, colorscale_flat)
map0.set_terrain_type(terrain_plains, colorscale_plains)
map0.max_number_of_rivers = 1
map0.max_number_of_roads = 1

map1 = MapInitializer("First demo map")
map1.chunk = (0,0)
map1.reverse_hmap = True
map1.world_size = (32,32)
map1.set_terrain_type(terrain_plains, colorscale_plains)
map1.max_number_of_roads = 1
# map1.zoom_cell_sizes = [64,32,16]
##map1.max_river_length = 100

map2 = MapInitializer("Second demo map")
map2.world_size = (256, 128) #with big maps it is better to use lower persistance
map2.persistance = 1.3 #The higher, the bigger are the "continents"
map2.palm_homogeneity = 0.9
map2.chunk = (12345,0)

map3 = MapInitializer("Third demo map")
map3.chunk = (6666,6666)
map3.world_size = (128,128)
map3.persistance = 1.5
#Note : it is better to start the cells sizes with a power of 2. Then it doesn't matter.
map3.zoom_cell_sizes = [32,20,8]
map3.max_number_of_roads = 0
