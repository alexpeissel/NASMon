# -*- coding: utf-8 -*-
"""
ImageComponent
Parses image files and outputs 1-bit byte arrays
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

from logzero import logger
from PIL import Image
from string import Template


class ImageComponent:
    def __init__(self, image_file, x, y, width=0, height=0, rotation=0, image_data=None):
        """
        Image Component
        Args:
            image_file: The source image file, (PNG only currently, XBM targeted next, other formats untested)
            x: The starting x coordinate, (0 is leftmost position)
            y: The starting y coordinate, (0 is highest position)
            width: The intended width of the image in pixels
            height: The intended width of the image in pixels
            rotation: The intended rotation in degrees of the image
            image_data: Instead of sourcing the PIL Image object from a file, use
        """
        self._MAX_WIDTH = 128
        self._MAX_HEIGHT = 32

        self.image_file = image_file
        self.image_data = image_data

        self._base_image = None
        self.sub_image_components = []

        self._updatable_values = {"image_file": self.image_file,
                                  "x": x, "y": y,
                                  "width": width,
                                  "height": height,
                                  "rotation": rotation}

        for key, value in self._updatable_values.iteritems():
            self.__dict__[key] = value

        # If the instance has been passed an image, (i.e. component is a sub-component) set the base image to the passed
        # in image.  Otherwise, assume that the component is the first instance and load in the image file as normal.
        if self.image_data:
            self._base_image = image_data
        else:
            self._base_image = Image.open(self.image_file)
            self.sub_image_components = self._generate_sub_image_components(self._base_image, width, height, rotation)

    def update(self, command_output):
        # Preserve the path of the exising file
        current_image_file = self._base_image

        # For each mutable value, update the instance __dict__ to the result of the template
        for key, value in self._updatable_values.iteritems():
            interpolated_value = Template(str(value)).safe_substitute(command_output)
            self.__dict__[key] = interpolated_value

        # If the file path has changed, update image_data to the new image
        if self.image_file is not current_image_file:
            self._base_image = Image.open(self.image_file)

    def get_bytes(self, encoding=None):
        output = self._base_image.tobytes()

        if encoding:
            output = output.encode(encoding)

        return output

    def _generate_sub_image_components(self, image, width=0, height=0, rotation=0, tile_width=8, tile_height=8):
        logger.debug("Converting image to a 1 bit")
        image = image.convert("1")

        logger.debug("Scaling image to %i x %i and rotating by %i degrees", width, height, rotation)
        transformed_image = self._transform_image(image, width, height, rotation)
        logger.debug("Splitting image into %i x %i tiles", tile_width, tile_height)
        sub_images = self._split_image(transformed_image, tile_width, tile_height)

        image_components = []

        # Create an image component for each tile
        for sub_image in sub_images:
            print sub_image
            image_components.append(ImageComponent(self.image_file,
                                                   self.x + sub_image.get("x"),
                                                   self.y + sub_image.get("y"),
                                                   sub_image.get("width"),
                                                   sub_image.get("height"),
                                                   rotation,
                                                   image_data=sub_image.get("image")))

        return image_components

    def _transform_image(self, image, width, height, rotation):
        size = (width, height)

        if width is 0:
            width_percent = (self._MAX_WIDTH / float(image.size[0]))
            updated_height = int((float(image.size[1]) * float(width_percent)))
            size = (self._MAX_WIDTH, updated_height)
            logger.debug("No size set, setting size to max, (width: %i, height: %i", self._MAX_WIDTH, self._MAX_HEIGHT)

        return image.resize(size, Image.NEAREST).rotate(rotation, expand=True)

    def _split_image(self, image, tiles_wide, tiles_high):
        image_width, image_height = image.size

        tiles = []

        for i in range(0, image_height, tiles_wide):
            for j in range(0, image_width, tiles_wide):
                box = (j, i, j + tiles_wide, i + tiles_high)
                cropped_image = image.crop(box).rotate(270)
                tiles.append({"image": cropped_image,
                              "width": cropped_image.size[0],
                              "height": cropped_image.size[1],
                              "x": j + tiles_wide,
                              "y": i + tiles_high})

        logger.debug("Split image into %i pieces", len(tiles))
        return tiles
