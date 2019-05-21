import pygame, thorpy

class Gui:

    def __init__(self, me):
        self.surface = thorpy.get_screen()
        self.cam = me.cam
        self.me = me


    def clear(self):
        self.cam.other_to_draw = []

    def draw_destinations(self, cell, color, alpha):
        if cell.unit:
            score = cell.unit.get_possible_destinations()
            s = pygame.Surface(self.me.cam.cell_rect.size)
            s.fill(color)
            s.set_alpha(alpha)
            for x,y in score:
                v = score[(x,y)]
                rect = self.me.cam.get_rect_at_coord((x,y))
                self.cam.other_to_draw.append((s,rect.topleft))
##                img = thorpy.make_text(str(v))
##                self.cam.other_to_draw.append((img.get_image(),rect.topleft))
    ##            print(score)
    ##            unit.move_to_cell(me.lm.cells[x+1][y])

    def lbm(self, e):
        self.clear()
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            color = (255,0,0)
            alpha = 100
            self.draw_destinations(cell, color, alpha)

    def mousemotion(self, e):
        self.clear()
        pos = e.pos
        cell = self.me.cam.get_cell(pos)
        if cell:
            color = (255,255,0)
            alpha = 100
            self.draw_destinations(cell, color, alpha)
