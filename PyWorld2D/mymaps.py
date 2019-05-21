from PyWorld2D.editor.mapbuilding import MapInitializer

#Here I simply define some properties of differnt maps. No programmation, just
#configuration.

#For a description of each parameter, please go the file ./editor/mapbuilding.py
#and have a look at the MapInitializer constructor

demo_map1 = MapInitializer("First demo map")
demo_map1.world_size = (32,32)
##demo_map1.max_river_length = 100

demo_map2 = MapInitializer("Second demo map")
demo_map2.world_size = (256, 128) #with big maps it is better to use lower persistance
demo_map2.persistance = 1.3 #The higher, the bigger are the "continents"
demo_map2.palm_homogeneity = 0.9
demo_map2.chunk = (12345,0)


demo_map3 = MapInitializer("Third demo map")
demo_map3.chunk = (6666,6666)
demo_map3.world_size = (128,128)
demo_map3.persistance = 1.5
#Note : it is better to start the cells sizes with a power of 2. Then it doesn't matter.
demo_map3.zoom_cell_sizes = [32,20,8]
demo_map3.max_number_of_roads = 20



