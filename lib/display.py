# -*- coding: utf-8 -*-

import colorsys
import numpy

class Color(object):

    red = None
    green = None
    blue = None

    hue = None
    saturation = None
    value = None

    alpha = None

    def __init__(self, red=None, green=None, blue=None, hue=None, saturation=None, value=None, alpha=None):

        rgb_passed = bool(red)|bool(green)|bool(blue)
        hsv_passed = bool(hue)|bool(saturation)|bool(value)

        if not alpha:
            alpha = 0.0

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

        super(Color, self).__setattr__('alpha', alpha)


    def __setattr__(self, key, value):

        if key in ('red', 'green', 'blue'):
            if value > 255.0:
                value = value % 255.0
            super(Color, self).__setattr__(key, value)
            self._update_hsv()

        elif key in ('hue', 'saturation', 'value'):
            if key == 'hue' and (value >= 360.0 or value < 0):
                value = value % 360.0
            elif key != 'hue' and value > 1.0:
                value = 1.0
            super(Color, self).__setattr__(key, value) 
            self._update_rgb()

        else:
            if key == 'alpha' and value > 1.0: # TODO: Might this be more fitting in another place?
                value = 1.0

            super(Color, self).__setattr__(key, value)


    def __repr__(self):

        return '<%s: red %f, green %f, blue %f, hue %f, saturation %f, value %f, alpha %f>' % (
                self.__class__.__name__,
                self.red,
                self.green,
                self.blue,
                self.hue,
                self.saturation,
                self.value,
                self.alpha
            )


    def __str__(self):
        return "%d %d %d" % (
            int(round(self.red * self.alpha)),
            int(round(self.green * self.alpha)),
            int(round(self.blue * self.alpha)),
        )


    def blend(self, other, mode='normal'):

        if self.alpha != 1.0: # no clue how to blend with a translucent bottom layer
            self.red = self.red * self.alpha
            self.green = self.green * self.alpha
            self.blue = self.blue * self.alpha

            self.alpha = 1.0

        if mode == 'normal':
            own_influence = 1.0 - other.alpha
            self.red = (self.red * own_influence) + (other.red * other.alpha)
            self.green = (self.green * own_influence) + (other.green * other.alpha)
            self.blue = (self.blue * own_influence) + (other.blue * other.alpha)


    def lighten(self, other):

        if isinstance(other, int) or isinstance(other, float):
            other = Color(red=other, green=other, blue=other, alpha=1.0)

        if self.alpha != 1.0:
            self.red = self.red * self.alpha
            self.green = self.green * self.alpha
            self.blue = self.blue * self.alpha

            self.alpha = 1.0

        red = self.red + (other.red * other.alpha)
        green = self.green + (other.green * other.alpha)
        blue = self.blue + (other.blue * other.alpha)

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
            other = Color(red=other, green=other, blue=other, alpha=1.0)

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



class Layer(list):


    def __init__(self, *args, **kw):

        size = 0 if not kw.has_key('size') else kw.pop('size')

        super(Layer, self).__init__(*args, **kw)

        for i in range(0, size):
            self.append(util.Color())


    def blend(self, other, mode='normal'):

        for idx in range(0, len(self)):

            try:
                color = other[idx]
            except IndexError:
                color = util.Color()

            self[idx].blend(color, mode=mode)


    def lighten(self, other):

        if isinstance(other, int) or isinstance(other, float):

            d = Layer()

            for spot in self:
                d.append(util.Color(red=other, green=other, blue=other, alpha=1.0))

            other = d

        idx = -1
        for spot in self:
            idx += 1
            try:
                color = other[idx]
            except IndexError:
                color = util.Color()

            self[idx].lighten(color)


    def darken(self, other):

        if isinstance(other, int) or isinstance(other, float):

            d = Layer()

            for spot in self:
                d.append(util.Color(red=other, green=other, blue=other, alpha=1.0))

            other = d

        idx = -1
        for spot in self:
            idx += 1
            try:
                color = other[idx]
            except IndexError:
                color = util.Color()

            self[idx].darken(color)


class Display(Layer):

    output = None
    layers = None
    successes = None
    failures = None

    def __init__(self, output, *args, **kw):

        if kw.has_key('layers'):
            self.layers = kw.pop('layers')
        else:
            self.layers = []

        super(Display, self).__init__(*args, **kw)

        idx = 0
        for color in self:
            self[idx].alpha = 1.0 # This is the canvas. It is not translucent.
            idx += 1

        self.output = output
        self.successes = 0
        self.failures = 0


    def update(self):

        self.darken(255)
        for layer in self.layers:
            self.blend(layer)


    def render(self):

        #for item in self:
            #print "render item: ", item.__repr__()
        line = 'FRAME %s\n' % (' '.join([str(item) for item in self]),)
        #print line
        self.output.write(line)
        resp = self.output.readline()

        if resp.startswith('OK'):
            self.successes += 1
        else:
            self.failures += 1
            print "Success count: %d" % (self.successes,)
            print "Failure count: %d" % (self.failures,)

            print "Failure rate: ", (float(self.failures) / float(self.successes + self.failures)) * 100
