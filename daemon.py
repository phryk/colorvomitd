# -*- coding: utf-8 -*-

from time import sleep

import serial
import multiprocessing
import numpy


class Collector(multiprocessing.Process):

    connection = None
    pcm_device = None

    window_size = None
    window = None

    def __init__(self, connection, pcm_device, window_size):

        super(Collector, self).__init__()
        self.connection = connection
        self.pcm_device = pcm_device
        self.window_size = window_size

        self.window = numpy.zeros(self.window_size)

    def run(self):
        print "run called"
        with open(self.pcm_device, 'r') as handle:
            print "opened handle"
            while True:
                self.test()
                sleep(0.1)

    def test(self):
        print "oink"


class Daemon(object):

    serial_device = None
    pcm_device = None
    baud = None
    window_size = None
    boot_sleep = None

    collector = None
    serial_line = None

    def __init__(self, serial_device, pcm_device, baud=None, window_size=None, boot_sleep=None):

        self.serial_device = serial_device
        self.pcm_device = pcm_device
        self.baud = baud
        self.window_size = window_size
        self.boot_sleep = boot_sleep
        
        self.collector = Collector("TODO: pass pipe conn", self.pcm_device, self.window_size)

    def connect(self):

        self.serial_line = serial.Serial(self.serial_device, self.baud, timeout=0.5)
        sleep(self.boot_sleep)

    def start(self):

        self.connect()
        self.collector.start()
