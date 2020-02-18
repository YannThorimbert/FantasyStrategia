import random, pygame, thorpy
import PyWorld2D.thornoise.purepython.noisegen as ng
import PyWorld2D.rendering.tilers.tilemanager as tm
from PyWorld2D.mapobjects.objects import MapObject
import PyWorld2D.mapobjects.objects as objs
from PyWorld2D.editor.mapeditor import MapEditor
from PyWorld2D import PW_PATH
from PyWorld2D.ia.path import BranchAndBoundForMap
import PyWorld2D.rendering.tilers.tilemanager as tm


terrain_small = {  "hdeepwater": 0.3, #deep water only below 0.4
                    "hwater": 0.4, #normal water between 0.4 and 0.55
                    "hshore": 0.5, #shore water between 0.55 and 0.6
                    "hsand": 0.6, #and so on...
                    "hgrass": 0.7,
                    "hrock": 0.8,
                    "hthinsnow": 0.9}

terrain_normal = {  "hdeepwater": 0.4, #deep water only below 0.4
                    "hwater": 0.55, #normal water between 0.4 and 0.55
                    "hshore": 0.6, #shore water between 0.55 and 0.6
                    "hsand": 0.62, #and so on...
                    "hgrass": 0.8,
                    "hrock": 0.83,
                    "hthinsnow": 0.9}

terrain_plains = {  "hdeepwater": 0.2, #deep water only below 0.2
                    "hwater": 0.3, #normal water between 0.2 and 0.35
                    "hshore": 0.4, #shore water between 0.3 and 0.4
                    "hsand": 0.48, #and so on...
                    "hgrass": 0.68,
                    "hrock": 0.78,
                    "hthinsnow": 0.9}

terrain_flat = {    "hdeepwater": 0.2, #deep water only below 0.4
                    "hwater": 0.35, #normal water between 0.4 and 0.55
                    "hshore": 0.4, #shore water between 0.55 and 0.6
                    "hsand": 0.42, #and so on...
                    "hgrass": 1.,
                    "hrock": 1.999,
                    "hthinsnow": 1.9999}

VON_NEUMAN = [(-1,0), (1,0), (0,-1), (0,1)]

class MapInitializer:

    def __init__(self, name):
        self.name = name #name of the map
        ############ terrain generation:
        self.world_size = (128,128) #in number of cells. Put a power of 2 for tilable maps
        self.chunk = (1310,14) #Kind of seed. Neighboring chunk give tilable maps.
        self.persistance = 2. #parameter of the random terrain generation.
        self.n_octaves = "max" #parameter of the random terrain generation.
        self.reverse_hmap = False #set to True to reverse height map
        self.colorscale_hmap = None #colorscale to use for the minimap
        ############ graphical options:
        self.zoom_cell_sizes = [32, 16, 8] #size of one cell for the different zoom levels.
        self.nframes = 16 #number of frames per world cycle (impacts memory requirement!)
        self.fps = 60 #frame per second
        self.menu_width = 200 #width of the right menu in pixels
        self.box_hmap_margin = 20 #padding of the minimap inside its box
        self.max_wanted_minimap_size = 64 #size of the MINIMAP in pixels
        ############ material options:
        #cell_radius = cell_size//radius_divider
        # change how "round" look cell transitions
        self.cell_radius_divider = 8
        #path or color of the image of the different materials
        self.water = PW_PATH + "/rendering/tiles/water1.png"
        self.sand = PW_PATH + "/rendering/tiles/sand1.jpg"
        self.grass = PW_PATH + "/rendering/tiles/grass.png"
        self.grass2 = PW_PATH + "/rendering/tiles/grass8.png"
        self.rock = PW_PATH + "/rendering/tiles/rock2.png"
        self.black = (0,0,0)
        self.white = (255,255,255)
        #mixed images - we superimpose different image to make a new one
        #the value indicated correspond
        self.deepwater= 127 #mix water with black : 127 is the alpha of black
        self.mediumwater= 50 #mix water with black : 50 is the alpha of black
        self.shore = 127 #mix sand with water : 127 is the alpha of water
        self.thinsnow = 200 #mix rock with white : 200 is the alpha of white
        #water movement is obtained by using shifts.
        #x-shift is dx_divider and y-shift is dy_divider. Unit is pixel.
        self.dx_divider = 10
        self.dy_divider = 8
        #here we specify at which altitude is each biome
        self.hdeepwater = 0.4 #deep water only below 0.4
        self.hwater = 0.55 #normal water between 0.4 and 0.55
        self.hshore = 0.6 #shore water between 0.55 and 0.6
        self.hsand = 0.62 #and so on...
        self.hgrass = 0.8
        self.hrock = 0.83
        self.hthinsnow = 0.9
        self.hsnow = float("inf")
        #precomputed tiles are used only if load_tilers=True is passed to build_materials()
        self.precomputed_tiles = PW_PATH + "/rendering/tiles/precomputed/"
        #NB : if you want to add your own materials, then you must write your
        #   own version of build_materials function below, and modify the above
        #   parameters accordingly in order to include the additional material
        #   or remove the ones you don't want.
        ############ static objects options:
        self.static_objects_n_octaves = None
        self.static_objects_persistance = 1.7
        self.static_objects_chunk = (12,24)
        #normal forest:
        self.forest_text = "forest"
        self.tree = PW_PATH + "/mapobjects/images/tree.png"
        self.tree_size = 1.5
        self.fir1 = PW_PATH + "/mapobjects/images/yar_fir1.png"
        self.fir1_size = 1.5
        self.fir2 = PW_PATH + "/mapobjects/images/yar_fir2.png"
        self.fir2_size = 1.5
        self.forest_max_density = 1 #integer : number of trees per world cell
        self.forest_homogeneity = 0.1
        self.forest_zones_spread = [(0.5,0.2)]
        #snow forest:
        self.firsnow = PW_PATH + "/mapobjects/images/firsnow2.png"
        self.firsnow_size = 1.
        self.forest_snow_text = "forest"
        self.forest_snow_max_density = 1
        self.forest_snow_homogeneity = 0.5
        self.forest_snow_zones_spread = [(0.5,0.2)]
        #palm forest:
        self.palm = PW_PATH + "/mapobjects/images/skeddles.png"
        self.palm_size = 1.7
        self.palm_text = "forest"
        self.palm_max_density = 1
        self.palm_homogeneity = 0.5
        self.palm_zones_spread = [(0., 0.05), (0.3,0.05), (0.6,0.05)]
        #other things:
        self.bush = PW_PATH + "/mapobjects/images/yar_bush.png"
        self.bush_size = 1.
        self.village1 = PW_PATH + "/mapobjects/images/house0.png"
        self.village2 = PW_PATH + "/mapobjects/images/house2.png"
        self.village3 = PW_PATH + "/mapobjects/images/house3.png"
        self.village1_size = 1.
        self.village2_size = 1.
        self.village3_size = 1.
        self.village_homogeneity = 0.05
##        self.village1 = PW_PATH + "/mapobjects/images/pepperRacoon.png
##        self.village2 = PW_PATH + "/mapobjects/images/rgbfumes1.png"
##        self.village3 = PW_PATH + "/mapobjects/images/rgbfumes2.png"
##        self.village3_size = 2.3
##        self.village4 = PW_PATH + "/mapobjects/images/rgbfumes3.png"
##        self.village4_size = 2.3
        # self.cobble = PW_PATH + "/mapobjects/images/cobblestone2.png"
        self.cobble = PW_PATH + "/rendering/tiles/dirt1.jpg"
        self.cobble_size = 1.
        self.bridge_h = PW_PATH + "/mapobjects/images/bridge_h.png"
        self.bridge_h_size = 1.
        self.bridge_v = PW_PATH + "/mapobjects/images/bridge_v.png"
        self.bridge_v_size = 1.
        #if you want to add objects by yourself, look at add_static_objects(self)
        self.min_road_length = 10
        self.max_road_length = 40
        self.max_number_of_roads = 5
        self.min_river_length = 10
        self.max_river_length = 80
        self.max_number_of_rivers = 5
        ############ End of user-defined parameters
        self.user_objects = []
        self._forest_map = None
        self._static_objs_layer = None
        self._objects = {}
        self.heights = []
        self.seed_static_objects = self.chunk

    def set_terrain_type(self, terrain_type, colorscale):
        for key in terrain_type:
            setattr(self, key, terrain_type[key])
        self.colorscale_hmap = colorscale

    def get_saved_attributes(self):
        attrs = [a for a in self.__dict__.keys() if not a.startswith("_")]
        attrs.sort()
        return attrs

    def get_image(self, me, name):
        value = getattr(self, name)
        if isinstance(value, str):
            return me.load_image(value)
        elif isinstance(value, tuple):
            return me.get_color_image(value)


    def configure_map_editor(self):
        """Set the properties of the map editor"""
        me = MapEditor(self.name)
        me.map_initializer = self
        me.box_hmap_margin = self.box_hmap_margin
        me.zoom_cell_sizes = self.zoom_cell_sizes
        me.nframes = self.nframes
        me.fps = self.fps
        me.box_hmap_margin = self.box_hmap_margin
        me.menu_width = self.menu_width
        me.max_wanted_minimap_size = self.max_wanted_minimap_size
        me.world_size = self.world_size
        me.chunk = self.chunk
        me.persistance = self.persistance
        me.n_octaves = self.n_octaves
        me.reverse_hmap = self.reverse_hmap
        me.colorscale_hmap = self.colorscale_hmap
        me.refresh_derived_parameters()
        return me

    def build_materials(self, me, fast, use_beach_tiler, load_tilers):
        """
        <fast> : quality a bit lower if true, loading time a bit faster.
        <use_beach_tiler>: quality much better if true, loading buch slower.
        Requires Numpy !
        <load_tilers> : use precomputed textures from disk. Very slow but needed if
        you don't have Numpy but still want beach_tiler.
        """
        #might be chosen by user:
        #cell_radius = cell_size//radius_divider
        # change how "round" look cell transitions
        cell_radius_divider = 8
        #we load simple images - they can be of any size, they will be resized
        water_img = self.get_image(me, "water")
        sand_img = self.get_image(me, "sand")
        grass_img = self.get_image(me, "grass")
        grass_img2 = self.get_image(me, "grass2")
        rock_img = self.get_image(me, "rock")
        black_img = self.get_image(me, "black")
        white_img = self.get_image(me, "white")
        #mixed images - we superimpose different image to make a new one
        deepwater_img = tm.get_mixed_tiles(water_img, black_img, self.deepwater)
        mediumwater_img = tm.get_mixed_tiles(water_img, black_img, self.mediumwater)
        shore_img = tm.get_mixed_tiles(sand_img, water_img, self.shore) # alpha of water is 127
        thinsnow_img = tm.get_mixed_tiles(rock_img, white_img, self.thinsnow)
        ##river_img = tm.get_mixed_tiles(rock_img, water_img, 200)
        river_img = shore_img
        #water movement is obtained by using a delta-x (dx_divider) and delta-y shifts,
        # here dx_divider = 10 and dy_divider = 8
        #hmax=0.1 means one will find deepwater only below height = 0.1
        ##deepwater = me.add_material("Very deep water", 0.1, deepwater_img, self.dx_divider, self.dy_divider)
        me.add_material("Deep water", self.hdeepwater, mediumwater_img, self.dx_divider, self.dy_divider)
        me.add_material("Water", self.hwater, water_img, self.dx_divider, self.dy_divider)
        me.add_material("Shallow water", self.hshore, shore_img, self.dx_divider, self.dy_divider)
        me.add_material("Sand", self.hsand, sand_img)
        me.add_material("Grass", self.hgrass, grass_img)
        ##me.add_material("Grass", 0.8, grass_img2, id_="Grass2")
        me.add_material("Rock", self.hrock, rock_img)
        me.add_material("Thin snow", self.hthinsnow, thinsnow_img)
        me.add_material("Snow", self.hsnow, white_img)
        #Outside material is mandatory. The only thing you can change is black_img
        outside = me.add_material("outside", -1, black_img)
        #this is the heavier computing part, especially if the maximum zoom is large:
        print("Building material couples")
        if load_tilers:
            load_tilers = self.precomputed_tiles
        me.build_materials(cell_radius_divider, fast=fast,
                            use_beach_tiler=use_beach_tiler,
                            load_tilers=load_tilers)
    ##                        load_tilers=PW_PATH + "/rendering/tiles/precomputed/")
        ##me.save_tilers(PW_PATH + "/rendering/tiles/precomputed/")
        ##import sys;app.quit();pygame.quit();sys.exit();exit()

    def add_object(self, obj_name, x, y, flip=False):
        self.user_objects.append((obj_name, (x,y), flip))


    def add_static_objects(self, me):
        #1) We use another hmap to decide where we want trees (or any other object)
        S = len(me.hmap)
        self._forest_map = ng.generate_terrain(S, n_octaves=self.static_objects_n_octaves,
                                            persistance=self.static_objects_persistance,
                                            chunk=self.static_objects_chunk)
        ng.normalize(self._forest_map)
        #we can use as many layers as we want.
        #self._static_objs_layer is a superimposed map on which we decide to blit some static objects:
        self._static_objs_layer = me.add_layer()
        #3) We build the objects that we want.
        # its up to you to decide what should be the size of the object (3rd arg)
        tree = MapObject(me,self.tree,self.forest_text,self.tree_size)
        tree.max_relpos = [0., 0.]
        fir1 = MapObject(me,self.fir1,self.forest_text,self.fir1_size)
        fir1.max_relpos = [0., 0.]
        fir2 = MapObject(me,self.fir2,self.forest_text,self.fir2_size)
        fir2.max_relpos = [0., 0.]
        firsnow = MapObject(me,self.firsnow,self.forest_snow_text,self.firsnow_size)
        firsnow.max_relpos = [0., 0.]
        fir1.set_same_type([fir2, firsnow])
        palm = MapObject(me,self.palm,self.palm_text,self.palm_size)
        palm.max_relpos[0] = 0.1 #restrict because they are near to water
        palm.min_relpos[0] = -0.1
        bush = MapObject(me,self.bush,"bush",self.bush_size)
        village1 = MapObject(me,self.village1, "village",self.village1_size)
        village2 = MapObject(me,self.village2, "village",self.village2_size)
        village3 = MapObject(me,self.village3, "village",self.village3_size)
        for v in [village1,village2,village3]:
            v.max_relpos = [0, 0.15]
            v.min_relpos = [0, 0.1]
        #
        cobble = MapObject(me,self.cobble,"cobblestone",self.cobble_size)
        cobble.is_ground = True
        bridge_h = MapObject(me,self.bridge_h,"bridge",self.bridge_h_size,
                                str_type="bridge_h")
        bridge_h.is_ground = True
        bridge_h.max_relpos = [0., 0.]
        bridge_h.min_relpos = [0., 0.]
        bridge_v = MapObject(me,self.bridge_v,"bridge",self.bridge_v_size,
                                str_type="bridge_v")
        bridge_v.is_ground = True
        bridge_v.max_relpos = [0.,0.]
        bridge_v.min_relpos = [0., 0.]
        self._objects = {"oak":tree, "fir1":fir1, "fir2":fir2, "firsnow":firsnow,
                        "palm":palm, "bush":bush, "village":village1,
                        "cobble":cobble, "bridge_h":bridge_h, "bridge_v":bridge_v}
        #4) we add the objects via distributors, to add them randomly in a nice way
        #normal forest
        distributor = objs.get_distributor(me, [fir1, fir2, tree],
                                            self._forest_map, ["Grass","Rock"])
        distributor.max_density = self.forest_max_density
        distributor.homogeneity = self.forest_homogeneity
        distributor.zones_spread = self.forest_zones_spread
        distributor.distribute_objects(self._static_objs_layer, exclusive=True)
        #more trees in plains
        distributor = objs.get_distributor(me, [tree], self._forest_map, ["Grass"])
        distributor.max_density = self.forest_max_density
        distributor.homogeneity = self.forest_homogeneity
        distributor.zones_spread = self.forest_zones_spread
        distributor.distribute_objects(self._static_objs_layer, exclusive=True)
        #snow forest
        distributor = objs.get_distributor(me, [firsnow, firsnow.flip()],
                                        self._forest_map, ["Thin snow","Snow"])
        distributor.max_density = self.forest_snow_max_density
        distributor.homogeneity = self.forest_snow_homogeneity
        distributor.zones_spread = self.forest_snow_zones_spread
        distributor.distribute_objects(self._static_objs_layer, exclusive=True)
        #palm forest
        distributor = objs.get_distributor(me, [palm, palm.flip()], self._forest_map, ["Sand"])
        distributor.max_density = self.palm_max_density
        distributor.homogeneity = self.palm_homogeneity
        distributor.zones_spread = self.palm_zones_spread
        distributor.distribute_objects(self._static_objs_layer, exclusive=True)
        #bushes
        distributor = objs.get_distributor(me, [bush], self._forest_map, ["Grass"])
        distributor.max_density = 2
        distributor.homogeneity = 0.2
        distributor.zones_spread = [(0., 0.05), (0.3,0.05), (0.6,0.05)]
        distributor.distribute_objects(self._static_objs_layer)
        #villages
        distributor = objs.get_distributor(me,
##                                [village1, village1.flip(), village2, village2.flip(),
##                                 village3, village3.flip(), village4, village4.flip()],
##                                [village1, village1.flip(), village2, village2.flip(), village3, village3.flip()],
                                    [village1, village1.flip()],
##                                 village3, village3.flip(), village4, village4.flip()],
                                self._forest_map, ["Grass"], limit_relpos_y=False)
        distributor.max_density = 1
        distributor.homogeneity = self.village_homogeneity
        distributor.zones_spread = [(0.1, 0.05), (0.2,0.05), (0.4,0.05), (0.5,0.05)]
        distributor.distribute_objects(self._static_objs_layer, exclusive=True)
        cobbles = [cobble, cobble.flip(True,False),
                    cobble.flip(False,True), cobble.flip(True,True)]
        ############################################################################
        #Here we show how to use the path finder for a given unit of the game
        #Actually, we use it here in order to build cobblestone roads on the map
        me.initialize_rivers()
        costs_materials_road = {name:1. for name in me.materials}
        costs_materials_road["Snow"] = 10. #unit is 10 times slower in snow
        costs_materials_road["Thin snow"] = 2. #twice slower on thin snow...
        costs_materials_road["Sand"] = 2.
        for name in me.materials:
            if "water" in name.lower():
                costs_materials_road[name] = 1.1
        river_type = me.object_types["river"]
        costs_objects_road = {bush.int_type: 2., #unit is 2 times slower in bushes
                                cobble.int_type: 0.9,
                                river_type:2.}
        #Materials allowed (here we allow water because we add bridges)
        possible_materials_road=list(me.materials)
        possible_objects_road=[cobble.int_type, bush.int_type,
                                village1.int_type, river_type]
        ########################################################################
        #now we build a path for rivers, just like we did with roads.
        costs_materials_river = {name:1. for name in me.materials}
        #Materials allowed (here we allow water because we add bridges)
        possible_materials_river=list(me.materials)
        possible_objects_river=[]
        river_img = me.get_material_image("Shallow water")
        random.seed(self.seed_static_objects)
        n_roads = 0
        n_rivers = 0
        imgs_river = {}
        lm = me.lm
        for dx in [-1,0,1]:
            for dy in[-1,0,1]:
                imgs_river[(dx,dy)] = tm.build_tiles(river_img, lm.cell_sizes,
                                            lm.nframes,
                                            dx*lm.nframes, dy*lm.nframes, #dx, dy
                                            sin=False)
        material_dict = get_materials_dict(lm)
        while n_roads < self.max_number_of_roads or n_rivers < self.max_number_of_rivers:
            if n_rivers < self.max_number_of_rivers:
                n_rivers += 1
                add_random_river(me, me.lm, material_dict, imgs_river,
                                    costs_materials_river,
                                    costs_objects_road,
                                    possible_materials_river,
                                    possible_objects_river,
                                    min_length=self.min_river_length,
                                    max_length=self.max_river_length)
            if n_roads < self.max_number_of_roads:
                n_roads += 1
                add_random_road(me.lm, self._static_objs_layer, cobbles,
                                    (bridge_h,bridge_v),
                                    costs_materials_road,
                                    costs_objects_road,
                                    possible_materials_road,
                                    possible_objects_road,
                                    min_length=self.min_road_length,
                                    max_length=self.max_road_length)

    def add_user_objects(self, me):
        for name,coord,flip in self.user_objects:
            obj = self._objects[name]
            cell = me.lm.get_cell_at(coord[0],coord[1])
            if flip:
                obj = obj.flip()
            obj = obj.add_copy_on_cell(cell, first=True)
            obj.randomize_relpos()
            #insert at the beginning because it is the last object
            #think e.g. of a wooden bridge over a river. What the unit sees is
            #the wooden bridge
##            self._static_objs_layer.static_objects.insert(0,obj)
            self._static_objs_layer.static_objects.append(obj)


    def build_map(self, me, fast=False, use_beach_tiler=True, load_tilers=False,
                    graphical_load=True):
        """
        <fast> : quality a bit lower if true, loading time a bit faster.
        <use_beach_tiler>: quality much better if true, loading buch slower.
        Requires Numpy !
        <load_tilers> : use precomputed textures from disk. Very slow but needed if
        you don't have Numpy but still want beach_tiler.
        """
        if graphical_load: #just ignore this - nothing to do with map configuration
            screen = thorpy.get_screen()
            screen.fill((255,255,255))
            loading_bar = thorpy.LifeBar.make(" ",
                size=(thorpy.get_screen().get_width()//2,30))
            loading_bar.center(element="screen")
            update_loading_bar(loading_bar, "Building height map...", 0., graphical_load)
        build_hmap(me)
        for x,y,h in self.heights:
            me.hmap[x][y] = h
        if graphical_load:
            img = thorpy.get_resized_image(me.original_img_hmap, screen.get_size(), max)
            screen.blit(img, (0,0))
            update_loading_bar(loading_bar,"Building tilers...",0.1,graphical_load)
        self.build_materials(me, fast, use_beach_tiler, load_tilers)
        update_loading_bar(loading_bar,"Building map surfaces...",0.2,graphical_load)
        build_lm(me)
        update_loading_bar(loading_bar,"Adding static objects...",0.3,graphical_load)
        self.add_static_objects(me)
        self.add_user_objects(me)
        #Now that we finished to add objects, we generate the pygame surface
        update_loading_bar(loading_bar, "Building surfaces", 0.9, graphical_load)
        me.build_surfaces()
        me.build_gui_elements()


    def h(self, x,y,h):
        if isinstance(h,str):
            h = getattr(self, "h"+h) - 0.001
        self.heights.append((x,y,h))

def update_loading_bar(loading_bar, text, progress, on):
    print(text)
    if on:
        loading_bar.set_text(text)
        loading_bar.set_life(progress)
        loading_bar.blit()
        pygame.display.flip()


def build_lm(me):
    """Build the logical map corresponding to me's properties"""
    lm = me.build_map() #build a logical map with me's properties
    lm.frame_slowness = 0.1*me.fps #frame will change every k*FPS [s]
    me.set_map(lm) #we attach the map to the editor

def build_hmap(me):
    """Build a pure height map"""
    hmap = me.build_hmap()
    ##hmap[2][1] = 0.7 #this is how you manually change the height of a given cell
    #Here we build the miniature map image
    img_hmap = ng.build_surface(hmap, me.colorscale_hmap)
    new_img_hmap = pygame.Surface(me.world_size)
    new_img_hmap.blit(img_hmap, (0,0))
    img_hmap = new_img_hmap
    me.build_camera(img_hmap)
    return hmap


def add_random_road(lm, layer,
                    cobbles, bridges,
                    costs_materials, costs_objects,
                    possible_materials, possible_objects,
                    min_length,
                    max_length):
    """Computes and draw a random road between two random villages."""
    print("     Building random road...")
    villages = [o for o in layer.static_objects if "village" in o.str_type]
    if not villages:
        return
    v1 = random.choice(villages)
    c1 = find_free_next_to(lm, v1.cell.coord)
    # c1 = v1.cell
    if c1:
        villages_at_right_distance = []
        for v2 in villages:
            if v2 is not v1:
                if min_length <= c1.distance_to(v2.cell) <= max_length:
                    villages_at_right_distance.append(v2)
        if villages_at_right_distance:
            v2 = random.choice(villages_at_right_distance)
            c2 = find_free_next_to(lm, v2.cell.coord)
            # c2 = v2.cell
        else:
            return
        if c2:
            sp = BranchAndBoundForMap(lm, c1, c2,
                                    costs_materials, costs_objects,
                                    possible_materials, possible_objects)
            path = sp.solve()
            draw_road(path, cobbles, bridges, lm)

def get_materials_dict(lm):
    d = {}
    for x in range(lm.nx):
        for y in range(lm.ny):
            mat = lm.cells[x][y].material.name.lower()
            if mat in d:
                d[mat].append((x,y))
            else:
                d[mat] = [(x,y)]
    return d

##def pick_one_cell(md, coord1, materials):
##    for mat in materials:
##        if mat in md:
##            return random.choice(md[mat])

def add_random_river(me, layer, material_dict,
                    imgs,
                    costs_materials, costs_objects,
                    possible_materials, possible_objects,
                    min_length, max_length):
    """Computes and draw a random river."""
    print("     Building random river...")
    lm = me.lm
    md = material_dict
    #1) pick one random end
    if "shallow water" in md:
        cell_end = random.choice(md["shallow water"])
    elif "grass" in md:
        cell_end = random.choice(md["grass"])
    elif "snow" in md:
        cell_end = random.choice(md["snow"])
    else:
        print("COULD FIND END")
        return
    #2) pick one random source
    if "snow" in md:
        cell_source = random.choice(md["snow"])
    elif "thin snow" in md:
        cell_source = random.choice(md["thin snow"])
    elif "rock" in md:
        cell_source = random.choice(md["rock"])
    else:
        print("COULD FIND SOURCE")
        return
    #3) verify distance
    cell_source = lm.cells[cell_source[0]][cell_source[1]]
    cell_end = lm.cells[cell_end[0]][cell_end[1]]
    if min_length <=  cell_source.distance_to(cell_end) <= max_length:
        pass
    else:
        print("TOO LONG")
        return
    sp = BranchAndBoundForMap(lm, cell_source, cell_end,
                            costs_materials, costs_objects,
                            possible_materials, possible_objects)
    path = sp.solve()
    #4) change the end to first shallow shore cell
    actual_path = []
    for cell in path:
        actual_path.append(cell)
        if "water" in cell.material.name.lower():
            break
        else:
            next_to_water = False
            for neigh in cell.get_neighbors_von_neuman():
                if neigh:
                    if "water" in neigh.material.name.lower():
                        next_to_water = True
                        break
            if next_to_water:
                break
    #
    objs = {}
    for key in imgs:
        river_obj = MapObject(me, imgs[key][0], "river", 1.)
        river_obj.is_ground = True
        objs[key] = river_obj
    #5) add river cells to map and layer
    for i,cell in enumerate(actual_path):
        dx,dy = get_path_orientation(i, cell, actual_path)
        c = objs.get((dx,dy))
        if not c:
            raise Exception("No river object for delta", dx, dy)
        c = c.add_copy_on_cell(cell)
        cell.name = "river"
        layer.static_objects.append(c)
    if path:
        print("RIVER BUILT:", [cell.coord for cell in path])
        return path



def find_free_next_to(lm, coord):
    ok = []
    for x,y in VON_NEUMAN:
        cell = lm.get_cell_at(coord[0]+x,coord[1]+y)
        if cell:
            if not cell.objects:
                if not cell.unit:
                    ok.append(cell)
    if ok:
        return random.choice(ok)


def get_path_orientation(i, cell, path):
    dx, dy = 0, 0
    if i > 0:
        dx += cell.coord[0] - path[i-1].coord[0]
        dy += cell.coord[1] - path[i-1].coord[1]
    if i + 1 < len(path):
        dx += path[i+1].coord[0] - cell.coord[0]
        dy += path[i+1].coord[1] - cell.coord[1]
    if dx > 0:
        dx = 1
    elif dx < 0:
        dx = -1
    if dy > 0:
        dy = 1
    elif dy < 0:
        dy = -1
    return dx, dy


def draw_path(path, objects, layer):
    """<path> is a list of cells"""
    for cell in path:
        c = random.choice(objects)
        c = c.add_copy_on_cell(cell)
        layer.static_objects.append(c)

def draw_road(path, cobbles, bridges, layer):
    """<path> is a list of cells"""
    for i,cell in enumerate(path):
        is_bridge =  "river" in [c.str_type for c in cell.objects]
        if is_bridge:
            dx,dy = get_path_orientation(i,cell,path)
            if dx != 0:
                c = bridges[0]
            elif dy != 0:
                c = bridges[1]
            else:
                c = random.choice(bridges)
                # raise Exception("Path orientation not expected:",dx,dy)
        else:
            c = random.choice(cobbles)
        c = c.add_copy_on_cell(cell)
        layer.static_objects.append(c)