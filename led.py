#!env python
# -*- coding:utf-8 -*-

#import numba # MORE MAGIC.

import multiprocessing
import time

from serial import Serial
from sys import exit

import util
import audio


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


class Pattern(Layer):

    #layer = None

    #def __init__(self, layer):

    #    super(Pattern, self).__init__()
    #    self.layer = layer

    def update(self):
        pass


class HSVRotate(Pattern):

    idx = None
    hue = None

    def __init__(self, *args, **kw):

        super(HSVRotate, self).__init__(*args, **kw)
        self.idx = 0
        self.hue = 0

    def update(self):

        spot = self[self.idx]
        if(self.hue >= 359):
            self.hue = 0
            self.idx += 1

            if self.idx >= len(self):
                self.idx = 0
        
            spot = self[self.idx]

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


    def __init__(self, color, step=3.6, spot_width=None, **kw):

        super(Irrlicht, self).__init__(**kw)

        self.deg = 0
        self.color = color
        self.step = step

        self.spot_distance = 360.0 / len(self)
        self.spot_coords = []

        for i in range(0, len(self)):
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

            spot = self[idx]
            spot.red = self.color.red #* multiplier
            spot.green = self.color.green #* multiplier
            spot.blue = self.color.blue #* multiplier
            spot.alpha = multiplier * self.color.alpha

            idx += 1


class Visualizer(Pattern):   

    def update(self, amplitudes):

        super(Visualizer, self).update()

        self[0].saturation = 1
        self[1].saturation = 1
        self[2].saturation = 1
        self[3].saturation = 1

        self[0].hue = 0
        self[1].hue = 90
        self[2].hue = 180
        self[3].hue = 270

        amps = util.octave_amplitudes(amplitudes, 4)
        self[0].value = amps[0]
        self[1].value = amps[1]
        self[2].value = amps[2]
        self[3].value = amps[3]


class Ravelicht(Irrlicht):

    smoothed_bass = None
    smoothed_mids = None
    smoothed_heights = None
    initial_hue = None

    def __init__(self, *args, **kw):

        super(Ravelicht, self).__init__(*args, **kw)

        self.smoothed_bass = 0
        self.smoothed_mids = 0
        self.smoothed_heights = 0
        self.initial_hue = self.color.hue 

    def update(self, amplitudes):

        bass, mids, heights = util.octave_amplitudes(amplitudes, 6)[0:3]
        self.smoothed_bass = (self.smoothed_bass * 0.9) + (bass * 0.1)
        self.color.hue = self.initial_hue + (self.smoothed_bass * 60) - 30
        self.color.value = self.smoothed_bass * 2
        self.step = self.smoothed_bass * 16

        super(Ravelicht, self).update()


class Ravelichter(Visualizer):

    basshue = 40
    midhue = 300
    trebhue = 240

    basslicht = None
    midlicht = None
    treblicht = None

    smoothed_bass = None
    smoothed_mids = None
    smoothed_heights = None

    def __init__(self, *args, **kw):

        super(Ravelichter, self).__init__(*args, **kw)

        self.basslicht = Irrlicht(color=util.Color(hue=self.basshue, saturation=1, value=1, alpha=1.0), size=len(self), spot_width=120)
        self.midlicht = Irrlicht(color=util.Color(hue=self.midhue, saturation=1, value=1, alpha=1.0), size=len(self), spot_width=90)
        self.midlicht.deg = 90
        self.treblicht = Irrlicht(color=util.Color(hue=self.trebhue, saturation=1, value=1, alpha=1.0), size=len(self), spot_width=90)
        self.treblicht.deg = 270

        self.smoothed_bass = 0
        self.smoothed_mids = 0
        self.smoothed_heights = 0


    def update(self, amplitudes):

        self.darken(255)
        bass, mids, heights, x, y, z = util.octave_amplitudes(amplitudes, 6)
        self.smoothed_bass = (self.smoothed_bass * 0.9) + (bass * 0.1)
        self.smoothed_mids = (self.smoothed_mids * 0.9) + (mids * 0.1)
        self.smoothed_heights = (self.smoothed_heights * 0.75) + (heights * 0.25)


        self.basslicht.color.hue = self.basshue + (self.smoothed_bass * 60) - 30
        self.basslicht.color.alpha = self.smoothed_bass * 6
        self.basslicht.step = self.smoothed_bass * -6

        self.midlicht.color.hue = self.midhue + (self.smoothed_mids * 60) - 30
        self.midlicht.color.alpha = self.smoothed_mids * 3
        self.midlicht.step = self.smoothed_mids * 3

        self.treblicht.color.hue = self.trebhue + (self.smoothed_heights * 60) - 30
        self.treblicht.color.alpha = self.smoothed_heights * 3
        self.treblicht.step = self.smoothed_heights * 3

        self.basslicht.update()
        self.midlicht.update()
        self.treblicht.update()

        self.blend(self.basslicht)
        self.blend(self.midlicht)
        self.blend(self.treblicht)


# temporary config, TODO: move into some sort of config file?
DEMO_OUTPUT = True
#SERIAL_DEVICE = '/dev/cuaU0'
SERIAL_DEVICE = '/dev/ttyUSB0'
BAUD = 57600
EMULATOR_WIDTH = 1024
EMULATOR_HEIGHT = 400

def main():


    if DEMO_OUTPUT:
        #from emulator import CombinedOutput # importing this without X fails
        #output = CombinedOutput(SERIAL_DEVICE, BAUD, width=EMULATOR_WIDTH, height=EMULATOR_HEIGHT)
        from emulator import Emulator # importing this without X fails
        output = Emulator(width=EMULATOR_WIDTH, height=EMULATOR_HEIGHT)
    else:
        output = Serial(SERIAL_DEVICE, BAUD, timeout=1.5)

    analyzer_read, analyzer_write = multiprocessing.Pipe(False)

    analyzer = audio.Analyzer(analyzer_write, '/mnt/a/mpd.fifo', window_size=4096, squelch=False, std=False)
    analyzer.start()
    print "Analyzer started."

    #layer_1 = Layer([util.Color(), util.Color(), util.Color(), util.Color()])
    #layer_2 = Layer([util.Color(), util.Color(), util.Color(), util.Color()])
    #layer_3 = Layer([util.Color(), util.Color(), util.Color(), util.Color()])
    #layer_4 = Layer([util.Color(), util.Color(), util.Color(), util.Color()])


    #pattern = HSVRotate(layer_1)

    # WHOOP WHOOP ITS DA LIGHT OF DA POLICE
    #pattern_1 = Irrlicht(layer_1, util.Color(hue=340, saturation=1, value=1), step=8, spot_width=140)
    #pattern_1.deg = 180
    #pattern_2 = Irrlicht(layer_2, util.Color(hue=200, saturation=1, value=1), step=8, spot_width=140)

    #pattern_1 = Irrlicht(layer_1, util.Color(hue=250, saturation=1, value=0.5), step=0.36, spot_width=270)
    #pattern_2 = Irrlicht(layer_2, util.Color(hue=30, saturation=1, value=0.8), step=0.36, spot_width=90)
    #pattern_2.deg = 180
    #pattern_3 = Irrlicht(layer_3, util.Color(hue=90, saturation=1, value=1.0), step=-0.2, spot_width=270)

    # water-ish
    #pattern_1 = Irrlicht(layer_1, util.Color(hue=200, saturation=1, value=0.2), step=2.17, spot_width=120)
    #pattern_2 = Irrlicht(layer_2, util.Color(hue=190, saturation=1, value=0.2), step=-4.23, spot_width=200)
    #pattern_3 = Irrlicht(layer_3, util.Color(hue=240, saturation=1, value=0.05), step=-16.1)
    #pattern_4 = Irrlicht(layer_4, util.Color(hue=170, saturation=1, value=0.05), step=18.3)

    # fire-ish
    #pattern_1 = Irrlicht(layer_1, util.Color(hue=20, saturation=1, value=0.2), step=2, spot_width=200)
    #pattern_1.deg = 180
    #pattern_2 = Irrlicht(layer_2, util.Color(hue=40, saturation=1, value=1), step=-4, spot_width=200)
    #pattern_3 = Irrlicht(layer_3, util.Color(hue=320, saturation=1, value=0.217), step=-16)
    #pattern_4 = Irrlicht(layer_4, util.Color(hue=40, saturation=1, value=0.264317), step=12)


    #pattern_1 = Ravelicht(4, util.Color(hue=40, saturation=1, value=1), spot_width=120)
    #pattern_2 = Irrlicht(layer_2, util.Color(hue=180, saturation=1, value=1), step=-14, spot_width=140)
    #pattern_2 = Visualizer(layer_2)
    
    pattern_1 = Ravelichter(size=4)

    display = Display(output, size=4, layers=[pattern_1])

    time.sleep(2)


    while True:

        if analyzer_read.poll():
            amplitudes = analyzer_read.recv()
            if DEMO_OUTPUT:
                #output.emulator.amplitudes = amplitudes
                output.amplitudes = amplitudes

            pattern_1.update(amplitudes)
            #pattern_2.update(amplitudes)
            #pattern_3.update()
            #pattern_4.update()

            display.update()
            display.render()


if __name__ == '__main__':

    main()
