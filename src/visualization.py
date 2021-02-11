from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math


class VisualizationStrategy(object):
    """Base class for the visualization strategies. It provides some functionality
    used by inheriting classes such as creating/saving the result image.
    """

    def __init__(self, width, height, heightmap, config):
        """Simply set the attributes which were passed as parameters."""
        self.width = width
        self.height = height
        self.img = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        self.config = config
        self.color_map = self.config['colors']
        self.heightmap = heightmap

    def visualize(self):
        """Wraps actual visualization which occurs in inheriting classes. This methods
        sets up the result image and the color maps. Inheriting classes must implement
        _visualize() where the actual visualization takes place and they may implement
        _pre_save_filter() to perform some operations before saving the image.
        """
        if 'filename' not in self.config:
            raise Exception('No image filename given.')
        filename = self.config['filename']

        if 'colors' not in self.config:
            raise Exception('No colormap given for rectangle visualization.')

        self._visualize()
        self._pre_save_filter()
        self.img.save(filename)

    def get_color(self, idx):
        """Simply return the color at the given index in the color map. A conversion to
           is necessary, because the type of idx is numpy.float64 (since it comes
           directly from the heightmap)
        """
        return self.color_map[int(idx)]

    def _visualize(self):
        """Dummy implementation of the actual visualization which takes place in the
           subclasses.
        """
        pass

    def _pre_save_filter(self):
        """Dummy implementation of pre-save operations called when a subclass does not
           override this method.
        """
        pass


class RectangleStrategy(VisualizationStrategy):
    """Provides a simple visualization strategy where each tile in the heightmap is
       represented by a rectangle.
    """

    def __init__(self, heightmap, config):
        """Constructor of the rectangle visualization strategy. The total width and
        height of the image depends on the side lengths of the rectangle which must
        be included in parameter _config_.
        """
        self.sidelen_x = config['sidelen_x']
        self.sidelen_y = config['sidelen_y']
        width = self.sidelen_x * heightmap.shape[0]
        height = self.sidelen_y * heightmap.shape[1]
        super(RectangleStrategy, self).__init__(width, height, heightmap, config)

    def _visualize(self):
        """Draws the individual tiles as rectangles on the image.
        """
        for ((i, j), g) in np.ndenumerate(self.heightmap):
            self.draw.rectangle([self.sidelen_x * i, self.sidelen_y * j,
                                 self.sidelen_x * (i + 1), self.sidelen_y * (j + 1)],
                                fill=self.get_color(g))


class HexagonStrategy(VisualizationStrategy):
    """Provides a slightly more complex visualization strategy than individual rectangles:
    Each tile is represented by a hexagon which are aligned in a typical grid pattern.
    """

    def __init__(self, heightmap, config):
        """Constructor of the hexagon visualization strategy. The total width and height
        of the image depends on the outer edge length of an individual hexagon which
        must be included in parameter _config_.
        """
        self.edgelen = config['edgelen']
        # note that edgelen * math.sqrt(3) is the 'inner' edge length of the hexagon
        width = int(math.ceil(self.edgelen * math.sqrt(3) * heightmap.shape[0] +
                              math.sqrt(3) / 2 * self.edgelen))
        height = int(math.ceil(1.5 * self.edgelen * heightmap.shape[1] + 0.5 * self.edgelen))
        super(HexagonStrategy, self).__init__(width, height, heightmap, config)

    @staticmethod
    def _gen_hexagon(initial, a):
        """Returns all points of a individual hexagon with the top-left point being
           parameter 'initial' and edge length 'a'
        """
        x, y = initial
        b = a * (math.sqrt(3) / 2)
        return [(int(math.ceil(xc)), int(math.ceil(yc))) for (xc, yc) in
                [(x, y), (x + b, y - 0.5 * a), (x + 2 * b, y),
                 (x + 2 * b, y + a), (x + b, y + 1.5 * a), (x, y + a)]]

    def _pre_save_filter(self):
        """Apply a smooth filter to soften the edges of the hexagons."""
        self.img = self.img.filter(ImageFilter.SMOOTH)

    def _visualize(self):
        """Draws the individual tiles as hexagons on the image."""
        for ((i, j), g) in np.ndenumerate(self.heightmap):
            offset_x = int(math.ceil(math.sqrt(3) / 2 * self.edgelen)) if j % 2 == 1 else 0
            hexagon = self._gen_hexagon((int(math.ceil(i * math.sqrt(3) *
                                                       self.edgelen + offset_x)),
                                         int(math.ceil(j * 1.5 * self.edgelen +
                                                       0.5 * self.edgelen))),
                                        self.edgelen)
            self.draw.polygon(hexagon, fill=self.get_color(g))
