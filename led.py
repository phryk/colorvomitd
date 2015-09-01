#!env python
# -*- coding:utf-8 -*-

import colorsys
import multiprocessing
import pyglet
import time

from serial import Serial
from sys import exit

import util
import audio


class Emulator(pyglet.window.Window):

    flag_send = None
    message = None
    colors = None
    amplitudes = None

    def __init__(self, *args, **kw):

        if not kw.has_key('config'):
            kw['config'] = pyglet.gl.Config(double_buffer=True, alpha_size=8)


        super(Emulator, self).__init__(*args, **kw)
        pyglet.gl.glEnable(pyglet.gl.GL_TEXTURE_2D)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glDisable(pyglet.gl.GL_DEPTH_TEST)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)

        self.flag_send = False
        self.colors = [Color(), Color(), Color(), Color()]


    def readline(self):
        return "OK"
        #if self.flag_send:
        #    return self.message

        #self.flag_send = False

    def write(self, request):

        tokens = request.split(' ')

        if tokens[0] == 'FRAME':

            idx = 0
            channels = tokens[1:]
            for channel in channels:
                try:
                    value = int(channel)
                    channels[idx] = value

                except Exception:
                    self.flag_send = True
                    self.message = 'You failed at supplying proper integer parameters'
                    return

                idx += 1

            led = 0
            chan = 0

            channel_names = ['red', 'green', 'blue']

            for value in channels:

                channel_name = channel_names[chan] 
                self.colors[led].__setattr__(channel_name, value)

                chan += 1

                if chan > 2:
                    chan = 0
                    led += 1

            #print "Updated colors: ", self.colors

            self.clear()
            self.update()


    def update(self):

        half_width = int(round(self.width / 2))
        half_height = int(round(self.height / 2))

        vertex_coords = [

            0, half_height + 1,
            half_width, half_height + 1,
            half_width, self.height,
            0, self.height,

            half_width + 1, half_height + 1,
            self.width, half_height + 1,
            self.width, self.height,
            half_width + 1, self.height,

            half_width + 1, 0,
            self.width, 0,
            self.width, half_height,
            half_width + 1, half_height,

            0,0,
            int(round(self.width / 2)), 0,
            int(round(self.width / 2)), int(round(self.height / 2)),
            0, int(round(self.height / 2))
        ]


        vertex_colors = []
        idx = 0
        for color in self.colors:

            vc = [color.red / 255.0, color.green / 255.0, color.blue / 255.0]

            vertex_colors += vc
            vertex_colors += vc
            vertex_colors += vc
            vertex_colors += vc

            idx += 1

        pyglet.graphics.draw(len(vertex_coords)/2, pyglet.gl.GL_QUADS,
            ('v2f', vertex_coords),
            ('c3f', vertex_colors)
        )

        if self.amplitudes is not None:

            x = 0
            y_bottom = 1
            
            spectrogram_vertices = []
            spectrogram_colors = []
            for amplitude in self.amplitudes:

                x+= 1
                y_top = amplitude * (self.height/2)

                spectrogram_vertices += [
                    x, y_bottom,
                    x+1, y_bottom,
                    x+1, y_top,
                    x, y_top
                ]

                spectrogram_colors += [
                    0.5, 0.5, 0.5, 0.5,
                    0.5, 0.5, 0.5, 0.5,
                    0.5, 0.5, 0.5, 0.8,
                    0.8, 0.5, 0.5, 0.8
                ]

#                pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
#                    ('v2f', [
#                        x, y_bottom,
#                        x+1, y_bottom,
#                        x+1, y_top,
#                        x, y_top
#                    ]),
#                    ('c4f', [
#                        0.5, 0.5, 0.5, 0.5,
#                        0.5, 0.5, 0.5, 0.5,
#                        0.5, 0.5, 0.5, 0.8,
#                        0.8, 0.5, 0.5, 0.8
#                    ])
#                )

            pyglet.graphics.draw(int(len(spectrogram_vertices) / 2), pyglet.gl.GL_QUADS, ('v2f', spectrogram_vertices), ('c4f', spectrogram_colors))


        pyglet.clock.tick()

        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')
            window.flip()


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


class Layer(list):

    def lighten(self, other):

        if isinstance(other, int) or isinstance(other, float):

            d = Layer()

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

            d = Layer()

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

        self.output = output
        self.successes = 0
        self.failures = 0


    def update(self):

        self.darken(255)
        for layer in self.layers:
            self.lighten(layer)


    def render(self):

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


class Pattern(object): # TODO: Make Pattern inherit from Layer!

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


class Visualizer(Pattern):   

    def update(self, amplitudes):

        super(Visualizer, self).update()

        self.display[0].saturation = 1
        self.display[1].saturation = 1
        self.display[2].saturation = 1
        self.display[3].saturation = 1

        self.display[0].hue = 0
        self.display[1].hue = 90
        self.display[2].hue = 180
        self.display[3].hue = 270

        amps = util.octave_amplitudes(amplitudes, 4)
        self.display[0].value = amps[0]
        self.display[1].value = amps[1]
        self.display[2].value = amps[2]
        self.display[3].value = amps[3]

class Ravelicht(Irrlicht):

    def update(self, amplitudes):

        bass, mid, heights = util.octave_amplitudes(amplitudes, 3)
        self.color.hue += bass * 36
        self.step = mid * 36

        super(Ravelicht, self).update()


if __name__ == '__main__':

    #output = Serial('/dev/cuaU1', 57600, timeout=1.5)
    output = Emulator(width=1024, height=600)

    analyzer_read, analyzer_write = multiprocessing.Pipe(False)

    analyzer = audio.Analyzer(analyzer_write, '/tmp/mpd.fifo', window_size=4096, std=128)
    analyzer.start()
    print "Analyzer started."

    layer_1 = Layer([Color(), Color(), Color(), Color()])
    layer_2 = Layer([Color(), Color(), Color(), Color()])
    layer_3 = Layer([Color(), Color(), Color(), Color()])
    layer_4 = Layer([Color(), Color(), Color(), Color()])
    display = Display(output, [Color(), Color(), Color(), Color()], layers=[layer_1, layer_2, layer_3, layer_4])
    #pattern = HSVRotate(layer_1)

    # WHOOP WHOOP ITS DA LIGHT OF DA POLICE
    #pattern_1 = Irrlicht(layer_1, Color(hue=340, saturation=1, value=1), step=8, spot_width=140)
    #pattern_1.deg = 180
    #pattern_2 = Irrlicht(layer_2, Color(hue=200, saturation=1, value=1), step=8, spot_width=140)

    #pattern_1 = Irrlicht(layer_1, Color(hue=250, saturation=1, value=0.5), step=0.36, spot_width=270)
    #pattern_2 = Irrlicht(layer_2, Color(hue=30, saturation=1, value=0.8), step=0.36, spot_width=90)
    #pattern_2.deg = 180
    #pattern_3 = Irrlicht(layer_3, Color(hue=90, saturation=1, value=1.0), step=-0.2, spot_width=270)

    # water-ish
    #pattern_1 = Irrlicht(layer_1, Color(hue=200, saturation=1, value=0.2), step=2.17, spot_width=120)
    #pattern_2 = Irrlicht(layer_2, Color(hue=190, saturation=1, value=0.2), step=-4.23, spot_width=200)
    #pattern_3 = Irrlicht(layer_3, Color(hue=240, saturation=1, value=0.05), step=-16.1)
    #pattern_4 = Irrlicht(layer_4, Color(hue=170, saturation=1, value=0.05), step=18.3)

    # fire-ish
    #pattern_1 = Irrlicht(layer_1, Color(hue=20, saturation=1, value=0.2), step=2, spot_width=200)
    #pattern_1.deg = 180
    #pattern_2 = Irrlicht(layer_2, Color(hue=40, saturation=1, value=1), step=-4, spot_width=200)
    #pattern_3 = Irrlicht(layer_3, Color(hue=320, saturation=1, value=0.217), step=-16)
    #pattern_4 = Irrlicht(layer_4, Color(hue=40, saturation=1, value=0.264317), step=12)


    pattern_1 = Ravelicht(layer_1, Color(hue=320, saturation=1, value=1), spot_width=120)
    #pattern_2 = Irrlicht(layer_2, Color(hue=180, saturation=1, value=1), step=-14, spot_width=140)
    #pattern_2 = Visualizer(layer_2)

    time.sleep(2)


    while True:

        if analyzer_read.poll():
            amplitudes = analyzer_read.recv() # not very elegant, but this lets us end up with the most current amplitude set and clears the pipes' queue
            if(isinstance(output, Emulator)):
                output.amplitudes = amplitudes

            pattern_1.update(amplitudes)
            #pattern_2.update(amplitudes)
            #pattern_3.update()
            #pattern_4.update()

            display.update()
            display.render()
