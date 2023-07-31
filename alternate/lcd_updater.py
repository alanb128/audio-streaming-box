#!/usr/bin/python3
#
# moOde audio player (C) 2014 Tim Curtis
# http://moodeaudio.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# Stub script for lcd-updater.sh daemon

#with open("/var/local/www/currentsong.txt") as file1:
#    with open("/home/pi/lcd.txt", "w") as file2:
#        for line in file1:
#            file2.write(line)

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Be sure to check the learn guides for more usage information.

This example is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!

Author(s): Melissa LeBlanc-Williams for Adafruit Industries
"""

import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341
from adafruit_rgb_display import st7789  # pylint: disable=unused-import
from adafruit_rgb_display import hx8357  # pylint: disable=unused-import
from adafruit_rgb_display import st7735  # pylint: disable=unused-import
from adafruit_rgb_display import ssd1351  # pylint: disable=unused-import
from adafruit_rgb_display import ssd1331  # pylint: disable=unused-import

def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

# Configuration for CS and DC pins (these are PiTFT defaults):
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()
# pylint: disable=line-too-long
# Create the display:
# disp = st7789.ST7789(spi, rotation=90,                            # 2.0" ST7789
# disp = st7789.ST7789(spi, height=240, y_offset=80, rotation=180,  # 1.3", 1.54" ST7789
# disp = st7789.ST7789(spi, rotation=90, width=135, height=240, x_offset=53, y_offset=40, # 1.14" ST7789
# disp = st7789.ST7789(spi, rotation=90, width=172, height=320, x_offset=34, # 1.47" ST7789
# disp = st7789.ST7789(spi, rotation=270, width=170, height=320, x_offset=35, # 1.9" ST7789
# disp = hx8357.HX8357(spi, rotation=180,                           # 3.5" HX8357
# disp = st7735.ST7735R(spi, rotation=90,                           # 1.8" ST7735R
# disp = st7735.ST7735R(spi, rotation=270, height=128, x_offset=2, y_offset=3,   # 1.44" ST7735R
# disp = st7735.ST7735R(spi, rotation=90, bgr=True,                 # 0.96" MiniTFT ST7735R
# disp = ssd1351.SSD1351(spi, rotation=180,                         # 1.5" SSD1351
disp = ssd1351.SSD1351(spi, height=96, width=128, y_offset=32, #rotation=180, # 1.27" SSD1351
# disp = ssd1331.SSD1331(spi, rotation=180,                         # 0.96" SSD1331
#disp = ili9341.ILI9341(
#    spi,
#    rotation=90,  # 2.2", 2.4", 2.8", 3.2" ILI9341
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)
# pylint: enable=line-too-long


# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
if disp.rotation % 180 == 90:
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
else:
    width = disp.width  # we swap height/width to rotate it to landscape!
    height = disp.height
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box as the background
draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
disp.image(image)

# Draw sections
draw.rectangle(
    (0, 0, width, 20), fill=(96, 96, 96)
)

draw.rectangle(
    (0, 77, width, height), fill=(96, 96, 96)
)


# Load a TTF Font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

d_artist = ""
d_title = ""
d_encode = ""
d_state = ""
d_time = ""
d_bitrate = ""
d_album = ""

# Get text
with open("/var/local/www/currentsong.txt") as file1:
    for line in file1:
        if left(line, 7) == "artist=":
            d_artist = line[7:]
        if left(line, 6) == "title=":
            d_title = line[6:]
        if left(line, 8) == "encoded=":
            d_encode = line[8:]
        if left(line, 8) == "bitrate=":
            d_bitrate = line[8:]
        if left(line, 6) == "state=":
            d_state = line[6:]
        if left(line, 6) == "album=":
            d_album = line[6:]

d_encode = d_encode[:-1]  # appears to have a newline at end, cutting it out
d_stream = "{0}, {1}".format(d_encode, d_bitrate)
d_state = d_state[:-1]  # appears to have a newline at end, cutting it out
d_artist = d_artist[:-1]

if d_artist == "Radio station":
    d_artist = d_album

# draw play or stop shape

if d_state == "stop":
    #print("draw stop")
    draw.rectangle(
    (2, 4, 12, 14), fill=(255, 128, 0)
)

if d_state == "pause":
    draw.rectangle(
    (2, 4, 6, 14), fill=(255, 128, 0)
)
    draw.rectangle(
    (8, 4, 12, 14), fill=(255, 128, 0)
)

if d_state == "play":
    draw.polygon([(2,4), (12,9), (2,14)], fill = (255,128,0))
# Draw Some Text

draw.text(
    (20, 2),
    d_stream,
    font=font,
    fill=(192, 192, 192),
)

draw.text(
    (2,25),
    d_title,
    font=font2,
    fill=(255, 128, 0),
)

draw.text(
    (2,50),
    d_artist,
    font=font2,
    fill=(224, 224, 224),
)

# Display image.
disp.image(image)
