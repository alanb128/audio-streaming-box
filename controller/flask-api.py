from flask import Flask, jsonify, request
from pad4pi import rpi_gpio
import time

import board
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd

from adafruit_seesaw import seesaw, rotaryio
import RPi.GPIO as GPIO

VERSION = 0.5

# Adafruit I2C QT Rotary Encoder
# Using the INT output on Pi GPIO 17
seesaw = seesaw.Seesaw(board.I2C(), addr=0x36)
seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
print("Found seesaw supported product {}".format(seesaw_product))
if seesaw_product != 4991:
    print("Wrong firmware loaded for QT encoder?  Expected 4991")
# Set up the rotary click button, and add to interrupt
seesaw.pin_mode(24, seesaw.INPUT_PULLUP)  # Pin on the QT
seesaw.set_GPIO_interrupts(1 << 24, True)
seesaw.enable_encoder_interrupt()

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

current_song = {"artist": "", "album": "", "title": "", "encoded": "", "bitrate": "", "volume": 0, "mute": 0, "state": ""}
display_mode = 0

def lcd_display(trigger):
    #
    # Decides what should be shown on the LCD display
    #
    
    lcd.clear()
    if trigger == "post":
        # moode status has changed
        if current_song["state"] == "stop":
            lcd.message = "     moOde\n    stopped"
        elif current_song["state"] == "pause":
            lcd.message = current_song["title"] + "\n\x01    paused"
        elif current_song["state"] == "play":
            lcd.message = current_song["title"] + "\n\x00 " + current_song["encoded"]
            
    elif trigger == "init":
        lcd.message = "     moOde\n     audio"

def key_handler(key):
    #
    # Catches any key presses and performs appropriate action
    #
    
    print("key pressed: {}".format(key))

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
            print("Button pressed!")
            #lcd.message = "Key pressed:\nRotary button"
            #button_rotary_click()
    else:
        if current_pos < rotary_pos:
            print("Turned right {}".format(current_pos))
            #lcd.message = "Rotary right: {}".format(current_pos)
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                #wheel_right()
                pass
        else:
            print("Turned left {}".format(current_pos))
            #lcd.message = "Rotary left: {}".format(current_pos)
            # Action on every other (even) click
            if (current_pos % 2) == 0:
                #wheel_left()
                pass
    rotary_pos = current_pos
    #print("seesaw rotary data updated! {0}, {1}".format(rot_pos, rot_btn))

app = Flask(__name__)

@app.route('/')
def get_api():
    return jsonify("this is the API")


@app.route('/', methods=['POST'])
def post_api():

    global current_song
    
    current_song["artist"] = request.form["artist"]
    current_song["album"] = request.form["album"]
    current_song["title"] = request.form["title"]
    current_song["encoded"] = request.form["encoded"]
    current_song["bitrate"] = request.form["bitrate"]
    current_song["volume"] = request.form["volume"]
    current_song["mute"] = request.form["mute"]
    current_song["state"] = request.form["state"]
    
    lcd_display("post")
    
    return '', 204


#  main thread of execution
if __name__=='__main__':

    lcd_display("init")
    
    #rotaryio interrupts
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(17, GPIO.FALLING, callback=rotary_incoming)

    # key_handler will be called each time a keypad button is pressed
    keypad.registerKeyPressHandler(key_handler)

    # Turn backlight on
    lcd.backlight = True

    # start API server
    app.run(host="0.0.0.0",port=5000,debug=True)

