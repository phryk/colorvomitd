# -*- coding: utf-8 -*-

import threading
import multiprocessing
import numpy
import time

from struct import unpack
from scipy.signal import gaussian, hann

class CircularList(list):

    size = None
    filled = None

    def __init__(self, size, *args, **kw):

        self.size = size
        self.filled = False

        super(CircularList, self).__init__(*args, **kw)


    def append(self, item):

        if len(self) == self.size:
            self.pop(0)

        elif len(self) == (self.size - 1):
            self.filled = True

        super(CircularList, self).append(item)


    def get_snapshot(self):

        return list(self)


class Collector(threading.Thread):

    read_size = None
    pcm_device = None
    window_size = None
    window = None


    def __init__(self, pcm_device, window_size=None, read_size=None):

        super(Collector, self).__init__()
        self.daemon = True

        self.pcm_device = pcm_device

        if not window_size:
            window_size = 4096

        if not read_size:
            read_size = 4

        self.window_size = window_size
        self.read_size = read_size

        self.window = CircularList(window_size)

    def run(self):

        handle = open(self.pcm_device, 'r')
        while True:
            chunk = handle.read(self.read_size * 2)
            raw_samples = [chunk[i:i+2] for i in range(0, self.read_size)]

            for raw_sample in raw_samples:
                self.window.append(unpack('<h', raw_sample)[0])


class Analyzer(multiprocessing.Process):

    connection = None
    pcm_device = None

    window_size = None
    collector = None
    std = None

    squelch = None
    amplitudes = None
    last_update = None

    def __init__(self, connection, pcm_device, window_size=None, read_size=None, squelch=None, std=None, *args, **kw):

        if std:
            self.std = std
        else:
            self.std = False
        self.max = 0 #TODO: Killme

        super(Analyzer, self).__init__(*args, **kw)
        self.daemon = True # Makes the parent kill this child process when the parent dies. Yay for infanticide! \o/
        self.connection = connection
        self.pcm_device = pcm_device
        self.window_size = window_size

        self.collector = Collector(self.pcm_device, window_size=self.window_size, read_size=read_size)
        self.squelch = squelch
        self.amplitudes = numpy.zeros(int(self.window_size / 4))
        self.last_update = 0


    def run(self):

        self.collector.start()

        while True:
            if self.collector.window.filled and time.time() - self.last_update >= 0.01: # at least 0.01 secs passed
                self.update_amplitudes()


    def update_amplitudes(self):

        frame = self.collector.window.get_snapshot()
        #frame = self.window

        if self.std > 0:
            frame = numpy.array(frame) * gaussian(len(frame), self.std)
        elif self.std < 0:
            frame = numpy.array(frame) * hann(len(frame))

        fft = numpy.abs(numpy.fft.rfft(frame))
        n = fft.size
        
        try:
            tm = numpy.max(fft[0:n/2])
            if tm > self.max:
                self.max = tm
                print self.max
            amplitudes = fft[0:n/2] / self.max
        #amplitudes = fft[0:n/2] / 3200000

        except Exception as e:
            print fft
            exit("Whoopsie!")
        #amplitudes = fft[0:n/2]

        clean_amplitudes = []

        if self.squelch:
            for amplitude in amplitudes:

                if not numpy.isnan(amplitude):
                    if self.squelch > amplitude:
                        amplitude = 0
                    clean_amplitudes.append(amplitude)

                else:
                    print "NAN in fft!"
                    raise OSError("OMGWTFMATE")
                    clean_amplitudes.append(numpy.float64(0))

            self.amplitudes = numpy.array(clean_amplitudes)

        else:
            self.amplitudes = amplitudes

        self.connection.send(self.amplitudes)

