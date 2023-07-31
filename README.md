# moode-box
Create a streaming music box with Moode audio, controls and an LCD

## Setup

In the moode UI, under "Local Services" in the "System" menu, turn on "Metadata file" and "LCD updater".


## Current Song

FYI: output of `cat  /var/local/www/currentsong.txt`:

```
file=NAS/Flacs/The Temptations/Vintage Gold/04 - Since I Lost My Baby.flac
artist=The Temptations
album=Vintage Gold
title=Since I Lost My Baby
coverurl=/coverart.php/NAS%2FFlacs%2FThe%20Temptations%2FVintage%20Gold%2F04%20-%20Since%20I%20Lost%20My%20Baby.flac
track=4
date=
composer=
encoded=File does not exist
bitrate=0 bps
outrate=0 bps
volume=100
mute=0
state=stop
```

```
/var/local/www/commandw/lcd_updater.py
/var/local/www/currentsong.txt
pi@moode-dev:~/moodisp $ cat  /var/local/www/currentsong.txt
file=https://ice.cr1.streamzilla.xlcdn.com:8000/sz=RCOLiveWebradio=mp3-192
artist=Radio station
album=RCO Live
title=Robert Schumann: Symphony No. 2 in C major, Op. 61 - RCO Amsterdam - John Eliot Gardiner (7.3.2010)
coverurl=imagesw%2Fradio-logos%2FRCO%20Live.jpg
track=
date=
composer=
encoded=VBR
bitrate=192 kbps
outrate=16 bit, 44.1 kHz, Stereo, 1.411 Mbps
volume=60
mute=0
state=play
```

## Alternate

This was the initial setup, using four pushbuttons and an [1.27" OLED screen](https://www.adafruit.com/product/1673).

To set this up, use raspi-config to turn on SPI for the screen. Then:

```
sudo pip3 install adafruit-circuitpython-rgb-display
sudo apt-get install fonts-dejavu
sudo apt-get install python3-pil #(Version: 8.1.2 already installed)
```

Update `/var/local/www/commandw/lcd_updater.py` with the code in this repo's alternate folder.
