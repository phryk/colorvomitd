# -*- coding: utf-8 -*-

import pyglet

import util

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
        self.colors = [util.Color(), util.Color(), util.Color(), util.Color()]


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
