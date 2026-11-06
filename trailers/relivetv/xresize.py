"""xresize.py NAME W H: resize the X11 window named NAME to W x H (client size) and print its frame window id."""
import sys
from Xlib import display, X
d = display.Display()
name, w, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
def find(win):
    try:
        if win.get_wm_name() == name and win.get_attributes().map_state == X.IsViewable:
            return win
    except Exception:
        pass
    for c in win.query_tree().children:
        r = find(c)
        if r: return r
win = find(d.screen().root)
win.configure(width=w, height=h, x=40, y=40)
d.sync()
print(hex(win.id))
