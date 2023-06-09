from flask import Flask, jsonify, request
from pad4pi import rpi_gpio
import time

import board
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd

from adafruit_seesaw import seesaw, rotaryio
import RPi.GPIO as GPIO

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

print("start")

def lcd_message(msg):
        lcd.clear()
        lcd.message = msg

def key_handler(key):

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

m_artist = ""
m_album = ""
m_title = ""
m_encoded = ""
m_bitrate = ""
m_volume = 0
m_mute = 0
m_state = ""

@app.route('/')
def get_api():
    return jsonify("this is the API")


@app.route('/', methods=['POST'])
def post_api():
    print("post")
    #post_data = request.get_json()
    m_artist = request.form["artist"]
    m_album = request.form["album"]
    m_title = request.form["title"]
    m_encoded = request.form["encoded"]
    m_bitrate = request.form["bitrate"]
    m_volume = request.form["volume"]
    m_mute = request.form["mute"]
    m_state = request.form["state"]
    print("title:{}".format(m_title))
    lcd_message(m_title + '\n' + m_encoded)
    #lcd_message("playing")
    return '', 204


#  main thread of execution
if __name__=='__main__':

    #rotaryio interrupts
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(17, GPIO.FALLING, callback=rotary_incoming)

    # printKey will be called each time a keypad button is pressed
    keypad.registerKeyPressHandler(key_handler)

    # Turn backlight on
    lcd.backlight = True

    # start API server
    app.run(host="0.0.0.0",port=5000,debug=True)
