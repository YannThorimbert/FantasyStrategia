import thorpy, random, pygame

##def draw_ashes(me, obj, n=40, frame=0):
##    ash_radius = 1
##    ash_color = (178, 190, 181)
##    ash_shades = [ash_color, tuple(a+30 for a in ash_color), tuple(a+60 for a in ash_color)]
##    ash_z =[]
##    ashlets_surf = pygame.Surface((3,3))
##    ashlets_surf.fill(ash_color)
##    for z in range(len(me.zoom_cell_sizes)):
##        ash_z.append([])
##        img = obj.imgs_z_t[z][frame]
##        ash = thorpy.graphics.get_shadow(img,
##                                        shadow_radius=ash_radius,
##                                        black=255,
##                                        color_format="RGBA",
##                                        alpha_factor=1.,
##                                        decay_mode="exponential",
##                                        color=ash_color,
##                                        sun_angle=45.,
##                                        vertical=True,
##                                        angle_mode="flip",
##                                        mode_value=(False, False))
##        w,h = ash.get_size()
##
##        for i in range(200):
##            x,y = random.randint(0,w-1), random.randint(0,h-1)
##            if ash.get_at((x,y)) == ash_color:
##                ash.set_at((x,y), random.choice(ash_shades))
##        ash_z[-1].append(ash)
##        ash_copy = ash.copy()
##        for i in range(n):
##            for i in range(180):
##                x,y = random.randint(0,w-1), random.randint(0,h-1)
##                ash_copy.set_at((x,y), (0,)*4)
##                x = int(random.gauss(w//2, w//8))
##                y = int(random.gauss(h, h//8))
##                ash_copy.set_at((x,y), random.choice(ash_shades))
####                ash_copy.blit(ashlets_surf, (x,y))
##            ash_z[-1].append(ash_copy.copy())
##    return ash_z


##def draw_ashes(me, obj, n=40, frame=0):
##    ash_radius = 1
##    ash_color = (178, 190, 181)
##    ash_shades = [ash_color, tuple(a+20 for a in ash_color), tuple(a-20 for a in ash_color)]
##    ashlets_surf = pygame.Surface((3,3))
##    ashlets_surf.fill(ash_color)
##    clock = pygame.time.Clock()
##    N = 120
##    cs = me.lm.get_current_cell_size()
##    rect, img = obj.get_fakerect_and_img(cs)
##    w,h = img.get_size()
##    w0,h0 = rect[0],rect[1]
##    for i in range(n):
##        clock.tick(30)
##        for k in range(N):
##            x,y = random.randint(w0,w0+w), random.randint(h0,h0+h)
##            me.screen.set_at((x,y), random.choice(ash_shades))
####                ash_copy.blit(ashlets_surf, (x,y))
##        pygame.display.flip()


def draw_ashes(me, obj, n=40, frame=0):
    ash_radius = 1
    ash_color = (178, 190, 181)
    ash_shades = [ash_color, tuple(a+30 for a in ash_color), tuple(a+60 for a in ash_color)]
    ash_z =[]
    ashlets_surf = pygame.Surface((3,3))
    ashlets_surf.fill(ash_color)
    clock = pygame.time.Clock()
    N = 180
    cs = me.lm.get_current_cell_size()
    rect, img = obj.get_fakerect_and_img(cs)
    w0,h0 = rect[0],rect[1]
    ash = thorpy.graphics.get_shadow(img,
                                    shadow_radius=ash_radius,
                                    black=255,
                                    color_format="RGBA",
                                    alpha_factor=1.,
                                    decay_mode="exponential",
                                    color=ash_color,
                                    sun_angle=45.,
                                    vertical=True,
                                    angle_mode="flip",
                                    mode_value=(False, False))
    w,h = ash.get_size()
    for i in range(200):
        x,y = random.randint(0,w-1), random.randint(0,h-1)
        if ash.get_at((x,y)) == ash_color:
            ash.set_at((x,y), random.choice(ash_shades))
    ###
    for i in range(n):
        for k in range(N):
            x,y = random.randint(0,w-1), random.randint(0,h-1)
            ash.set_at((x,y), (0,)*4)
            x = int(random.gauss(w//2, w//8))
            y = int(random.gauss(h, h//8))
            ash.set_at((x,y), random.choice(ash_shades))
##                ash_copy.blit(ashlets_surf, (x,y))
        me.draw()
        me.screen.blit(ash, rect)
        pygame.display.flip()
        clock.tick(30)


