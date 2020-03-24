import thorpy, random, pygame
from pygame.math import Vector2 as V2


class GameSmoke:

    def __init__(self, cam, sg, coord, delta):
        self.cam = cam
        self.sg = sg
        self.coord = coord
        self.delta = delta
        self.pos = None
        self.refresh_pos()

    def refresh_pos(self):
        self.pos = self.cam.get_rect_at_coord(self.coord).center
        cs = self.cam.cell_rect.w
        print("***", self.pos, self.delta, cs)
        if self.delta:
            x = self.pos[0]+self.delta[0]*cs
            y = self.pos[1]+self.delta[1]*cs
            self.pos = (x,y)

    def generate(self):
        self.refresh_pos()
        print(self.pos)
        self.sg.generate(self.pos)

smokegen_small = None
smokegen_small_vel = V2(0.5,-3)
smokegen_large = None
smokegen_large_vel = V2(1,-6)
smokegen_mod = 6

def initialize_smokegens():
    global smokegen_small, smokegen_large
    smokegen_small = thorpy.fx.get_fire_smokegen(n=50, color=(200,255,155),
                                            grow=0.5, black_increase_factor=2.)
    smokegen_large = thorpy.fx.get_fire_smokegen(n=50, color=(200,255,155),
                                            grow=1., black_increase_factor=2.)

def refresh_smokes(game):
    if game.t%smokegen_mod == 0:
        smokegen_small.kill_old_elements()
        smokegen_large.kill_old_elements()
        for s in game.smokes_log.values():
            s.generate()
        smokegen_small.update_physics(smokegen_small_vel)
        smokegen_large.update_physics(smokegen_large_vel)
    smokegen_small.draw(game.me.screen)
    smokegen_large.draw(game.me.screen)


def draw_ashes(game, obj, n=20, frame=0):
    global smokegen_mod
    tmp = smokegen_mod
    smokegen_mod = 2
    me = game.me
    ash_radius = 1
    ash_color = (178, 190, 181)
    N = 180
    ashlet_size = (2,2)
    ash_shades = [tuple(a-60 for a in ash_color),
                  tuple(a-90 for a in ash_color),
                  tuple(a-120 for a in ash_color)]
    ash_z =[]
    ashlets = [pygame.Surface(ashlet_size) for i in ash_shades]
    for i,c in enumerate(ash_shades):
        ashlets[i].fill(c)
    clock = pygame.time.Clock()
    cs = me.lm.get_current_cell_size()
    rect, img = obj.get_fakerect_and_img(cs)
    ash = thorpy.graphics.get_shadow(img,
                                    shadow_radius=ash_radius,
                                    black=255,
                                    color_format="RGBA",
                                    alpha_factor=1.,
                                    decay_mode="exponential",
                                    color=ash_shades[0],
                                    sun_angle=45.,
                                    vertical=True,
                                    angle_mode="flip",
                                    mode_value=(False, False))
    w,h = ash.get_size()
    for i in range(200):
        x,y = random.randint(0,w-1), random.randint(0,h-1)
        if ash.get_at((x,y)) == ash_shades[0]:
            ash.set_at((x,y), random.choice(ash_shades))
    ###
    for i in range(n):
        for k in range(N):
            x,y = random.randint(0,w-1), random.randint(0,h-1)
            ash.set_at((x,y), (0,)*4)
            x = int(random.gauss(w//2, w//8))
            y = int(random.gauss(h, h//8))
##            ash.set_at((x,y), random.choice(ash_shades))
            ash.blit(random.choice(ashlets), (x,y))
        me.draw()
        me.screen.blit(ash, rect)
        pygame.display.flip()
        clock.tick(30)
    smokegen_mod = tmp


