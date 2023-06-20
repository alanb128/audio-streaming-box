from flask import Flask, jsonify, request
from pad4pi import rpi_gpio
import time

import board
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd

from adafruit_seesaw import seesaw, rotaryio
import RPi.GPIO as GPIO

import requests
import os
import socket

VERSION = 0.5
DISPLAY_RESUME = 2.66  # seconds

no_rotary = True

# Adafruit I2C QT Rotary Encoder
# Using the INT output on Pi GPIO 17
try:
    seesaw = seesaw.Seesaw(board.I2C(), addr=0x36)
except:
    print("No rotary encoder - skipping...")
else:
    seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
    print("Found seesaw supported product {}".format(seesaw_product))
    if seesaw_product != 4991:
        print("Wrong firmware loaded for QT encoder?  Expected 4991")
    # Set up the rotary click button, and add to interrupt
    seesaw.pin_mode(24, seesaw.INPUT_PULLUP)  # Pin on the QT
    seesaw.set_GPIO_interrupts(1 << 24, True)
    seesaw.enable_encoder_interrupt()
    no_rotary = False

rotary_pos = 0  # keeps track of wheel position

# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2

# Initialise I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
#i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
#i2c = busio.I2C(board.SCL, board.SDA)

# Initialise the lcd class
lcd = character_lcd.Character_LCD_I2C(i2c, lcd_columns, lcd_rows)

# Custom chars
CHAR_PLAY = bytes([0x10,0x18,0x1c,0x1e,0x1c,0x18,0x10,0x0])
CHAR_PAUSE = bytes([0x0,0x1b,0x1b,0x1b,0x1b,0x1b,0x0,0x0])
CHAR_STOP = bytes([0x0,0x1f,0x1f,0x1f,0x1f,0x1f,0x0,0x0])
CHAR_BAR = bytes([0x0,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f])
lcd.create_char(0, CHAR_PLAY)
lcd.create_char(1, CHAR_PAUSE)
lcd.create_char(2, CHAR_STOP)
lcd.create_char(3, CHAR_BAR)

# to display play char: \x00

KEYPAD = [
        ["A","B","C","D"],
        ["E","F","G","H"],
        ["J","K","L","M"],
        ["N","P","Q","R"],
        ["T","U","V","W"]
]

ROW_PINS = [14,15,13,23,26] # BCM numbering
COL_PINS = [16,12,25,24] # BCM numbering

factory = rpi_gpio.KeypadFactory()

# Try factory.create_4_by_3_keypad
# and factory.create_4_by_4_keypad for reasonable defaults
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)

current_song = {"artist": "", "album": "", "title": "", "encoded": "", "bitrate": "", "volume": 0, "mute": 0, "state": "", "hostname": "hostname", "ip": "ip", "moode": "moode"}
display_mode = 0
playlists = []
preset_keys = ["T", "N", "J", "E", "A", "U", "P", "K", "F", "B"]
current_playlist = ""  # current or most recently played playlist
sel_playlist = ""   # selected playlist before being played
last_key = ""  # help with double key press issue
last_key_count = 0  # also help with double key
current_volume = 0
line_1_mode = "title"
line_2_mode = "normal"

def lcd_display(trigger):
    #
    # Decides what should be shown on the LCD display
    #
    
    my_display = "     moOde\n     audio"  # default if no trigger
    #print("trig: {0}, l1m: {1}, l2m: {2}".format(trigger, line_1_mode, line_2_mode))
    lcd.clear()
    if trigger == "resume":
        get_current_state()
        
    if trigger == "post" or trigger == "resume":
        if current_song["state"] == "stop":
            my_display = "     moOde\n    stopped"
        else:   # pause or play
            if line_1_mode == "title":
                my_display = current_song["title"]
            elif line_1_mode == "artist":
                my_display = current_song["artist"]
            elif line_1_mode == "album":
                my_display = current_song["album"]
            
            if current_song["state"] == "pause":
                my_display = my_display + "\n\x01    paused"
            elif current_song["state"] == "play":
                my_display = my_display +  "\n\x00 " + current_song["encoded"]
            
    elif trigger == "init":
        my_display = "     moOde\n     audio"
        
    elif (trigger == "info"):
        if line_2_mode == "info1":
            my_display = current_song["hostname"] + "\n" + current_song["ip"]
        elif line_2_mode == "info2":
            my_display = "moOde version:\n" + current_song["moode"]

    lcd.message = my_display
    
def sanitizer(mystring):
    #
    # removes anything but letters and numbers from input string
    # strings from moode can contain all kinds of garbage
    #
    out_string = ''
    for i in mystring:
        s = ord(i)
        if (s > 31) and (s < 127):
            out_string = out_string + i

    return out_string

def get_current_state():
    #
    # get current state from moode api
    #
    global current_song, current_volume
    
    r = requests.get('http://host.docker.internal/command/?cmd=get_currentsong')
    current = r.json()
    current_song["artist"] = sanitizer(current["artist"])
    current_song["album"] = sanitizer(current["album"])
    current_song["title"] = sanitizer(current["title"])
    current_song["encoded"] = sanitizer(current["encoded"])
    current_song["bitrate"] = sanitizer(current["bitrate"])
    current_song["volume"] = sanitizer(current["volume"])
    current_song["mute"] = sanitizer(current["mute"])
    current_song["state"] = sanitizer(current["state"])
    # below not exposed by moode api
    #current_song["hostname"] = current["h_name"]
    #current_song["moode"] = current["moode_ver"]
    #current_song["ip"] = current["ip"]

    current_volume = int(current_song["volume"])

def key_handler(key):
    #
    # Catches any key presses and performs appropriate action
    # T N J E A U P K F B H
    #
    global sel_playlist, current_playlist, line_1_mode, line_2_mode
    print("key: {}".format(key))
    if key in preset_keys:   # select/deselect a playlist
        if preset_keys.index(key) + 1 > len(playlists):
            lcd.clear()
            lcd.message = "No playlist\ndefined..."
            time.sleep(DISPLAY_RESUME)
            lcd_display("resume")
        else:
            if sel_playlist == playlists[preset_keys.index(key)]:
                # same playlist button clicked so deselect it
                lcd.clear()
                lcd.message = "Playlist\nunselected"
                sel_playlist = ""
            else:
                sel_playlist = playlists[preset_keys.index(key)]
                lcd.clear()
                lcd.message = "Play playlist?\n" + playlists[preset_keys.index(key)]
    elif key == "D":    # play/pause or play selected playlist
        if sel_playlist == "":
            get_current_state()
            if current_song["state"] == "play":
                # pause
                r = requests.get('http://host.docker.internal/command/?cmd=pause')
                #print("from PLAY state to PAUSE")
            elif current_song["state"] == "stop" or current_song["state"] == "pause":
                # play
                r = requests.get('http://host.docker.internal/command/?cmd=play')
                #print("From {} to PLAY".format(current_song["state"]))
            #lcd_display("resume")
        else:
            lcd.clear()
            lcd.message = "Please wait..."
            playlist(sel_playlist)
            current_playlist == sel_playlist
            sel_playlist = "" 
            lcd_display("resume")   
    elif key =="M":   # line 1 display
        if line_1_mode == "title":
            line_1_mode = "artist"
        elif line_1_mode == "artist":
            line_1_mode = "album"
        elif line_1_mode == "album":
            line_1_mode = "title"
        lcd_display("resume")
        
    elif key == "W":    #  line 2 display
        if line_2_mode == "normal":
            #print("x1")
            line_2_mode = "info1"
            lcd_display("info")
        elif line_2_mode == "info1":
            #print("x2")
            line_2_mode = "info2"
            lcd_display("info")
        elif line_2_mode == "info2":
            #print("x3")
            line_2_mode = "normal"
            lcd_display("resume")
            
    elif key == "H":
        if no_rotary:
            pass
        else:
            r = requests.get('http://host.docker.internal/command/?cmd=prev')
            
    elif key == "V":
        if no_rotary:
            pass
        else:
            r = requests.get('http://host.docker.internal/command/?cmd=next')

def adj_vol(direction):
    #
    #  changes volume level - expects "left" or "right"
    #
    global current_volume

    vol_level = ""
    v = round(current_volume/15) + 1
    #print("volume: {0} - {1}".format(v, current_volume))
    #for i in range(v):
    #     vol_level = vol_level + "\x03"
    vol_level = "\x03" * v
    #print("volume: {}".format(v))
    vol_level = vol_level.ljust(16)
    #print("vol level: {}".format(vol_level))
    lcd.message = "Volume          \n" + vol_level
    if direction == "left":
        current_volume = current_volume - 1
        r = requests.get('http://host.docker.internal/command/?cmd=vol.sh%20-dn%201')
    else:
        current_volume = current_volume + 1
        r = requests.get('http://host.docker.internal/command/?cmd=vol.sh%20-up%201')

def rotary_incoming(r):
    #
    # Triggerd by rotary QT interrupt
    # when rotary wheel is turned or clicked
    #
    global rotary_pos
    current_pos = seesaw.encoder_position()
    rot_btn = seesaw.digital_read(24)
    if rotary_pos == current_pos:
        if rot_btn == True:
            pass
            #print("Button pressed!")
            #lcd.message = "Key pressed:\nRotary button"
            #button_rotary_click()
    else:
        if current_pos < rotary_pos:
            pass
            #print("Turned right {}".format(current_pos))
            #lcd.message = "Rotary right: {}".format(current_pos)
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                adj_vol("right")
        else:
            pass
            #print("Turned left {}".format(current_pos))
            #lcd.message = "Rotary left: {}".format(current_pos)
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                adj_vol("left")
    rotary_pos = current_pos
    #print("seesaw rotary data updated! {0}, {1}".format(rot_pos, rot_btn))

def get_playlists():
    #
    # get playlists and add to dict for preset buttons
    #
    
    p = []
    
    url="http://host.docker.internal/command/playlist.php?cmd=get_playlists"
    cookies = {'PHPSESSID': 'ho7vk67sqrjua8sme0pqhsjgdq'}
    headers = {"Content-type": "application/json","Accept": "application/json"}
    r = requests.get(url, headers=headers, cookies=cookies)
    playlists = r.json()
    for playlist in playlists:
        for attribute, value in playlist.items():
            if attribute == "name":
                p.append(value)
                
    return p
    
def playlist(playlist):
    #
    # Plays a playlist
    #
    r = requests.get('http://host.docker.internal/command/?cmd=clear')
    r = requests.get('http://host.docker.internal/command/?cmd=load%20'+playlist)
    r = requests.get('http://host.docker.internal/command/?cmd=play')



app = Flask(__name__)

@app.route('/')
def get_api():
    return jsonify("this is the API")


@app.route('/', methods=['POST'])
def post_api():

    global current_song, current_volume
    
    current_song["artist"] = sanitizer(request.form["artist"])
    current_song["album"] = sanitizer(request.form["album"])
    current_song["title"] = sanitizer(request.form["title"])
    current_song["encoded"] = sanitizer(request.form["encoded"])
    current_song["bitrate"] = sanitizer(request.form["bitrate"])
    current_song["volume"] = sanitizer(request.form["volume"])
    current_song["mute"] = sanitizer(request.form["mute"])
    current_song["state"] = sanitizer(request.form["state"])
    current_song["hostname"] = request.form["h_name"]
    current_song["moode"] = request.form["moode_ver"]
    current_song["ip"] = request.form["ip"]

    current_volume = int(current_song["volume"])
    #print("h, m, i: {0} - {1} - {2}".format(current_song["hostname"], current_song["moode"], current_song["ip"]))
    lcd_display("post")
    
    return '', 204


#  main thread of execution

# Turn backlight on
lcd.backlight = True

lcd_display("init")

get_current_state()

playlists = get_playlists()

#rotaryio interrupts
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(17, GPIO.FALLING, callback=rotary_incoming)

# key_handler will be called each time a keypad button is pressed
keypad.registerKeyPressHandler(key_handler)

lcd_display("post")

# start API server
app.run(host="0.0.0.0",port=5000,debug=True,use_reloader=False)





