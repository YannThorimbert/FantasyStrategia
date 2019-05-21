from thorpy._utils.images import load_image
from pygame import surfarray
import math, pygame
from PyWorld2D.rendering.tilers.basetiler import BaseTiler

class RoundTiler(BaseTiler):

    def __init__(self, c, s, c_colorkey=None, s_colorkey=None):
        BaseTiler.__init__(self, c, c_colorkey)
        if isinstance(s, str):
            self.original_s = load_image(s, s_colorkey)
        else:
            self.original_s = s
        self.s = self.original_s.copy() #current center
        if self.s.get_size() != self.c.get_size():
            self.s = pygame.transform.scale(self.s, self.c.get_size())

    def scale_base(self, size):
        if size != self.original_img.get_size():
            self.c = pygame.transform.scale(self.original_img, size)
            self.s = pygame.transform.scale(self.original_s, size)

    def build_tiles(self, radius, background):
        self.imgs["s"] = self.s
        BaseTiler.build_tiles(self, radius, background)

    def make(self, size, radius, scale_first=True):
        if scale_first:
            self.scale_base(size)
        self.build_tiles(radius, background=None)
        if not scale_first:
            self.scale_base(size)
            self.scale_all_to_c()

    def cut_side(self, side, radius, background):
        #version for color background
        surf =  self.s.copy()
        w,h = self.c.get_size()
        rect = surf.get_rect()
        if "top" in side:
            rect = pygame.Rect(0, radius, w, h-radius)
        if "bottom" in side:
            rect = rect.clip(pygame.Rect(0, 0, w, h-radius))
        if "left" in side:
            rect = rect.clip(pygame.Rect(radius, 0, w-radius, h))
        if "right" in side:
            rect = rect.clip(pygame.Rect(0, 0, w-radius, h))
        surf.blit(self.c, rect.topleft, rect)
        return surf

    def get_round(self, radius, background):
        #version for color background
        w,h = self.c.get_size()
        surface = self.c.copy()
        inner = self.c.get_rect().inflate((-4*radius, -4*radius))
        b_c_rgb = surfarray.pixels3d(surface)
        s_rgb = surfarray.pixels3d(self.s)
        rngs = [(inner.x,inner.y,0,inner.x,0,inner.y),
                (inner.right,inner.y,inner.right,w,0,inner.y),
                (inner.x,inner.bottom,0,inner.x,inner.bottom,h),
                (inner.right,inner.bottom,inner.right,w,inner.bottom,h)]
        for x0,y0,xi,xf,yi,yf in rngs:
            for x in range(xi,xf):
                for y in range(yi,yf):
                    if math.sqrt((x-x0)**2 + (y-y0)**2) > radius:
                        b_c_rgb[x][y] = s_rgb[x][y]
        return surface

    def get_antiround(self, radius, background):
        w,h = self.c.get_size()
        surface = self.c.copy()
        b_c_rgb = surfarray.pixels3d(surface)
        s_rgb = surfarray.pixels3d(self.s)
        rngs = [(0,0,0,radius,0,radius),
                (w,0,w-radius,w,0,radius),
                (0,h,0,radius,h-radius,h),
                (w,h,w-radius,w,h-radius,h)]
        for x0,y0,xi,xf,yi,yf in rngs:
            for x in range(xi,xf):
                for y in range(yi,yf):
                    if math.sqrt((x-x0)**2 + (y-y0)**2) < radius:
                        b_c_rgb[x][y] = s_rgb[x][y]
        return surface
