## Alternate

This was the initial setup, using four pushbuttons and an [1.27" OLED screen](https://www.adafruit.com/product/1673).

Using the [Split Body Case DIY 4.72 x 3.82 x 1.57 inch enclosure](https://www.amazon.com/gp/product/B010DHQPVW) and replacing the front and back panel with the 3d printed STL files in the "alternate" folder.

A "power on" momentary pushbutton sends GPIO 3 to ground. The display uses a [3.3v L4931 voltage regulator](https://www.adafruit.com/product/2166) and a 10uf 50v capacitor to provide additional 3v power to the LCD since the HiFiberry Digi2-Pro has 3V current restrictions.

To set this up, use raspi-config to turn on SPI for the screen. Then:

```
sudo pip3 install adafruit-circuitpython-rgb-display
sudo apt-get install fonts-dejavu
sudo apt-get install python3-pil #(Version: 8.1.2 already installed)
```

Update `/var/local/www/commandw/lcd_updater.py` with the code in this repo's alternate folder.
