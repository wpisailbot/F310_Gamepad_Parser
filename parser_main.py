#!/usr/bin/python
############ Logitech F310 Gamepad Controller Main - parser_main.py ##########
# Original Author: John Zeller
# Description: Parser_Main polls the data in a python dictionary to check the
#         states of several buttons coming from parser_core.py. Once it
#         reads these states, it will display them for reference on the
#         terminal it was launched in

### NOTES #####################################################################
# 1) LEAVE MODE 'OFF' there is no support in parser_main.py for MODE ON
# 2) Naturally the gamepad sends the following values:
#   LJ/RJ - Down: 0-127
#   LJ/RJ - Up: 255-128
#   LJ/RJ - Left: 255-128
#   LJ/RJ - Right: 0-127
###############################################################################

### Buttons/Joys Represented: #################################################
# A, B, X, Y, RB, LB, LJButton, RJButton, Back, Start, Middle
# RT, LT, LeftJoy, RightJoy, Left, Right, Up, Down
###############################################################################

import sys
sys.path.append("./core")
import threading
from bus import *
from parser_core import *
import time
import numpy as np
from websocket import create_connection

class ParserMain(threading.Thread):
  def __init__(self):
    self.rudder = 0.
    self.winch = 0.
    self.winch_cnt = 0
    self.up = True
    self.ws = create_connection("ws://" + sys.argv[1] + ":13000")
    # Create bus object
    self.bus = Bus()
    # Create a dictionary to be used to keep states from joy_core
    self.states = { 'A':0, 'B':0, 'X':0, 'Y':0,             \
        'Back':0, 'Start':0, 'Middle':0,             \
        'Left':0, 'Right':0, 'Up':0, 'Down':0,         \
        'LB':0, 'RB':0, 'LT':0, 'RT':0,            \
        'LJ/Button':0, 'RJ/Button':0,             \
        'LJ/Left':0, 'LJ/Right':0, 'LJ/Up':0, 'LJ/Down':0,   \
        'RJ/Left':0, 'RJ/Right':0, 'RJ/Up':0, 'RJ/Down':0,  \
        'Byte0':0, 'Byte1':0, 'Byte2':0, 'Byte3':0,      \
        'Byte4':0, 'Byte5':0, 'Byte6':0, 'Byte7':0,      \
        'Byte0/INT':0, 'Byte1/INT':0, 'Byte2/INT':0,     \
        'Byte3/INT':0, 'Byte4/INT':0, 'Byte5/INT':0,     \
        'Byte6/INT':0, 'Byte7/INT':0}
    # Launch Parser_Core as a seperate thread to parse the gamepad
    self.parsercore = ParserCore(self.bus, self.states)

  def run(self):
    # Description: Polls the gamepad states and displays their current
    #         values on a simple Tkinter GUI

    # Launch simple GUI with Tkinter (Native GUI on Python)
    while True:
      self.parsercore.run()
      self.ws.send(self.create_msg())
      print(self.create_msg())

  def create_msg(self):
    rudder = self.states['RJ/Left'] + self.states['RJ/Right']
    deadband_radius = 20.0
    rudder -= deadband_radius * np.sign(rudder) # Get rid of deadband
    rudder = -rudder / (127. - deadband_radius) # Scale to -1 to 1
    rudder *= 0.5 # Scale to useful values of rudder
    winch = self.states['LJ/Left'] + self.states['LJ/Right']
    winch = -winch * 6. / 127.
    ballast = self.states['RT'] - self.states['LT']
    ballast = ballast * 90. / 255.
    string = '{"manual_sail_cmd":{"voltage":%f},"manual_rudder_cmd":{"pos":%f}, "manual_ballast_cmd":{"vel":%f}' % (winch, rudder, ballast)
    # 1 = auto, 4 = Filtered RC, 2 = WiFi, 3 = disabled
    mode = 2 if self.states['Y'] else 4 if self.states['B'] else 1 if self.states['A'] else 3 if self.states['X'] else None
    if mode != None:
      string += ',"control_mode":{"rudder_mode":%d,"winch_mode":%d,"ballast_mode":%d}' % (mode, mode, mode)
    elif self.states['RB']:
      string += ',"control_mode":{"rudder_mode":2,"winch_mode":1}'
    string += "}"
    return string

if __name__ == '__main__':
        parser = ParserMain()
        parser.run()
