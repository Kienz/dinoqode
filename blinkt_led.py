#!/usr/bin/env python
# coding: utf8
#
# Copyright (c) 2019 Stefan Kienzle
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import colorsys
import time
import argparse
from sys import exit

try:
    import blinkt
except ImportError:
    exit('This script requires the blinkt module\nInstall with: curl https://get.pimoroni.com/blinkt | bash')

try:
    import numpy as np
except ImportError:
    exit('This script requires the numpy module\nInstall with: sudo pip install numpy')

# Parse the command line arguments
arg_parser = argparse.ArgumentParser(description='Flash the Blinkt! led indicators.')
arg_parser.add_argument('--brightness', default=0.1, help='brightness (0..1) of the led lights', type=float)
arg_parser.add_argument('--color', default='0,128,0', help='color (r,g,b) of the led lights')
args = arg_parser.parse_args()
print(args)


blinkt.set_clear_on_exit(True)
blinkt.set_brightness(args.brightness)


# Convert rgb color to hsv values (rgb string have to be converted into array of float values)
hsv = colorsys.rgb_to_hsv(*([float(x) for x in args.color.split(',')]))
print(hsv)


# Blinkt example pulse.py
# https://github.com/pimoroni/blinkt/blob/master/examples/pulse.py
def make_gaussian(fwhm):
    x = np.arange(0, blinkt.NUM_PIXELS, 1, float)
    y = x[:, np.newaxis]
    x0, y0 = 3.5, 3.5
    fwhm = fwhm
    gauss = np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / fwhm ** 2)
    return gauss


while True:
    for z in list(range(1, 10)[::-1]) + list(range(1, 10)):
        fwhm = 5.0 / z
        gauss = make_gaussian(fwhm)
        start = time.time()
        y = 4

        for x in range(blinkt.NUM_PIXELS):
            h = hsv[0] # Hue (°)
            s = hsv[1] # Saturation (%)
            v = gauss[x, y] # Value (%)
            rgb = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = [int(255.0 * i) for i in rgb]
            blinkt.set_pixel(x, r, g, b)

        blinkt.show()
        end = time.time()
        t = end - start

        if t < 0.04:
            time.sleep(0.04 - t)
