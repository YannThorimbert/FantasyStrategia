import os
import sys

PW_PATH = os.path.abspath(os.path.dirname(__file__))
##PW_PATH = "./" #for py2exe
try:
    os.environ['PATH'] = ';'.join((PW_PATH, os.environ['PATH']))
    sys.path.append(PW_PATH)
except Exception:
    print("Couldn't add PyWorld2D to sys.path...\nPath : " + PW_PATH)


import PyWorld2D.editor
import PyWorld2D.gui
import PyWorld2D.ia
import PyWorld2D.mapobjects
import PyWorld2D.rendering
import PyWorld2D.saveload
import PyWorld2D.thornoise

#import PyWorld2D.example
