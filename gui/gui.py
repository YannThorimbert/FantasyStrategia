import pygame

def lbm(e, me):
    pos = e.pos
    cell = me.cam.get_cell(pos)
    x,y = cell.coord
    if cell.unit:
        unit = cell.unit
        unit.move_to_cell(me.lm.cells[x+1][y])

    me.draw()
    pygame.display.flip()
    # print(cell.coord, cell.h, cell.get_altitude(), cell.objects)
    # for obj in cell.objects:


    # me.lm.get_cell_at(15,15).objects
