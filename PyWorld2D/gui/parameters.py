import thorpy, pygame

DELAY_HELP = 5.

#cam
RMOUSE_COLOR = (255,255,255)

#cursor
CURSOR_COLOR_SELECT = (255,0,0)
CURSOR_COLOR_NORMAL = (255,255,0)

#titles
TFS = thorpy.style.TITLE_FONT_SIZE
TFC = thorpy.style.TITLE_FONT_COLOR

#normal
NFS = thorpy.style.FONT_SIZE
NFC = thorpy.style.FONT_COLOR

#small
SFS = NFS - 2
SFC = NFC

#highlight
HFS = NFS + 1
HFC = (255,0,0)

#info
IFS = NFS
IFC = (100,255,100)


#environments:
##env = {"small":-3, "normal":0, "large":+3, "highlight":+1}

def get_title(text):
    return thorpy.make_text(text, TFS, TFC)

def get_text(text):
    return thorpy.make_text(text, NFS, NFC)

def get_small_text(text):
    return thorpy.make_text(text, SFS, SFC)

def get_highlight_text(text):
    return thorpy.make_text(text, HFS, HFC)

def get_info_text(text):
    return thorpy.make_text(text, IFS, IFC)

def get_button(text, func, params=None):
    b = thorpy.make_button(text, func, params)
    b.set_font_size(NFS)
    b.set_font_color(NFC)
    return b

def get_small_button(text, func, params=None):
    b = thorpy.make_button(text, func, params)
    b.set_font_size(SFS)
    b.set_font_color(SFC)
    return b