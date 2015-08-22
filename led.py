#!env python
# -*- coding:utf-8 -*-

import colorsys

from serial import Serial
from time import sleep


class Color(object):

    red = None
    green = None
    blue = None

    hue = None
    saturation = None
    value = None

    def __init__(self, red=None, green=None, blue=None, hue=None, saturation=None, value=None):

        rgb_passed = bool(red)|bool(green)|bool(blue)
        hsv_passed = bool(hue)|bool(saturation)|bool(value)

        if rgb_passed and hsv_passed:
            raise ValueError("Color can't be initialized with RGB and HSV at the same time.")

        elif hsv_passed:

            if not hue:
                hue = 0.0
            if not saturation:
                saturation = 0.0
            if not value:
                value = 0.0

            super(Color, self).__setattr__('hue', hue)
            super(Color, self).__setattr__('saturation', saturation)
            super(Color, self).__setattr__('value', value)
            self._update_rgb()

        else:

            if not red:
                red = 0
            if not green:
                green = 0
            if not blue:
                blue = 0

            super(Color, self).__setattr__('red', red)
            super(Color, self).__setattr__('green', green)
            super(Color, self).__setattr__('blue', blue)
            self._update_hsv()


    def __setattr__(self, key, value):

        if key in ('red', 'green', 'blue'):
            if value > 255.0:
                value = value % 255.0
            super(Color, self).__setattr__(key, value)
            self._update_hsv()

        elif key in ('hue', 'saturation', 'value'):
            if key == 'hue' and value >= 360.0:
                value = value % 360.0
            super(Color, self).__setattr__(key, value) 
            self._update_rgb()


    def __repr__(self):

        return '<%s: red %f, green %f, blue %f, hue %f, saturation %f, value %f>' % (
                self.__class__.__name__,
                self.red,
                self.green,
                self.blue,
                self.hue,
                self.saturation,
                self.value
            )


    def __str__(self):
        return "%d %d %d" % (
            int(round(self.red)),
            int(round(self.green)),
            int(round(self.blue)),
        )


    def lighten(self, other):

        if isinstance(other, int) or isinstance(other, float):
            other = Color(red=other, green=other, blue=other)

        red = self.red + other.red
        green = self.green + other.green
        blue = self.blue + other.blue

        if red > 255.0:
            red = 255.0

        if green > 255.0:
            green = 255.0

        if blue > 255.0:
            blue = 255.0

        self.red = red
        self.green = green
        self.blue = blue


    def darken(self, other):

        if isinstance(other, int) or isinstance(other, float):
            other = Color(red=other, green=other, blue=other)

        red = self.red - other.red
        green = self.green - other.green
        blue = self.blue - other.blue

        if red < 0:
            red = 0

        if green < 0:
            green = 0

        if blue < 0:
            blue = 0

        self.red = red
        self.green = green
        self.blue = blue


    def _update_hsv(self):

        hue, saturation, value = colorsys.rgb_to_hsv(self.red/255.0, self.green/255.0, self.blue/255.0)
        super(Color, self).__setattr__('hue', hue * 360.0)
        super(Color, self).__setattr__('saturation', saturation)
        super(Color, self).__setattr__('value', value)


    def _update_rgb(self):

        red, green, blue = colorsys.hsv_to_rgb(self.hue / 360.0, self.saturation, self.value)
        super(Color, self).__setattr__('red', red * 255.0)
        super(Color, self).__setattr__('green', green * 255.0)
        super(Color, self).__setattr__('blue', blue * 255.0)


class Display(list):

    conn = None
    successes = None
    failures = None

    def __init__(self, conn, *args, **kw):

        super(Display, self).__init__(*args, **kw)
        self.conn = conn
        self.successes = 0
        self.failures = 0

    def render(self):

        line = 'FRAME %s\n' % (' '.join([str(item) for item in self]),)
        #print line
        self.conn.write(line)
        resp = self.conn.readline()

        if resp.startswith('OK'):
            self.successes += 1
        else:
            self.failures += 1
            print "Success count: %d" % (self.successes,)
            print "Failure count: %d" % (self.failures,)

            print "Failure rate: ", (float(self.failures) / float(self.successes + self.failures)) * 100


    def lighten(self, other):

        if isinstance(other, int) or isinstance(other, float):

            d = Display(None)

            for spot in self:
                d.append(Color(red=other, green=other, blue=other))

            other = d

        idx = -1
        for spot in self:
            idx += 1
            try:
                color = other[idx]
            except IndexError:
                color = Color()

            self[idx].lighten(color)


    def darken(self, other):

        if isinstance(other, int) or isinstance(other, float):

            d = Display(None)

            for spot in self:
                d.append(Color(red=other, green=other, blue=other))

            other = d

        idx = -1
        for spot in self:
            idx += 1
            try:
                color = display[idx]
            except IndexError:
                color = Color()

            self[idx].darken(color)


class Pattern(object):

    display = None

    def __init__(self, display):

        super(Pattern, self).__init__()
        self.display = display

    def update(self):
        pass


class HSVRotate(Pattern):

    idx = None
    hue = None

    def __init__(self, display):

        super(HSVRotate, self).__init__(display)
        self.idx = 0
        self.hue = 0

    def update(self):

        spot = self.display[self.idx]
        if(self.hue >= 359):
            self.hue = 0
            self.idx += 1

            if self.idx >= len(self.display):
                self.idx = 0
        
            spot = self.display[self.idx]

        else:
            self.hue += 1

        spot.hue = self.hue
        spot.saturation = 0.5
        spot.value = 0.5



class Irrlicht(Pattern):

    deg = None
    color = None
    spot_width = None
    spot_distance = None # distance between spots
    spot_coords = None


    def __init__(self, display, color, step=3.6, spot_width=None):

        super(Irrlicht, self).__init__(display)

        self.deg = 0
        self.color = color
        self.step = step

        self.spot_distance = 360.0 / len(self.display)
        self.spot_coords = []

        for i in range(0, len(self.display)):
            self.spot_coords.append(i * self.spot_distance)

        if spot_width:
            self.spot_width = spot_width
        else:
            self.spot_width = self.spot_distance



#    def __setattr__(self, key, value):
#
#        super(Irrlicht, self).__setattr__(key, value)
#
#        if key == 'deg':
#            self._update_gradient()


    def update(self):

        self.deg += self.step

        if self.step > 0 and self.deg > 360.0:
            self.deg = self.deg % 360.0

        elif self.step < 0 and self.deg < 0:
            self.deg += 360

        idx = 0
        for coord in self.spot_coords:

            distance = abs(self.deg - coord)

            if distance > 180:
                distance = 360.0 - distance

            if distance == 0:
                multiplier = 1.0
            elif distance >= self.spot_width:
                multiplier = 0.0
            else:
                multiplier = abs(distance - self.spot_width) / self.spot_width

            spot = self.display[idx]
            spot.red = self.color.red * multiplier
            spot.green = self.color.green * multiplier
            spot.blue = self.color.blue * multiplier

            idx += 1




if __name__ == '__main__':

    conn = Serial('/dev/cuaU1', 57600, timeout=1.5)
    display = Display(conn, [Color(), Color(), Color(), Color()])
    overlay_1 = Display(None, [Color(), Color(), Color(), Color()])
    overlay_2 = Display(None, [Color(), Color(), Color(), Color()])
    #pattern = HSVRotate(overlay_1)
    pattern_1 = Irrlicht(overlay_1, Color(hue=340, saturation=1, value=0.01), spot_width=60, step=1.2)
    pattern_2 = Irrlicht(overlay_2, Color(hue=200, saturation=1, value=1), step=-1.2, spot_width=135)
    #pattern_1 = Irrlicht(overlay_1, Color(red=255, green=96, blue=0), step=-0.4, spot_width=90)
    #pattern_2 = Irrlicht(overlay_2, Color(red=0, green=96, blue=255), step=1.2, spot_width=135)

    sleep(2)

    while True:

        display.darken(255) # reset main display

        pattern_1.update()
        pattern_2.update()

        display.lighten(overlay_1)
        display.lighten(overlay_2)
        display.render()
        sleep(0.01)
