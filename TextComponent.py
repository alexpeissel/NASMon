# -*- coding: utf-8 -*-
"""
TextComponent
Describes a string of text that can be drawn on the display
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

from logzero import logger
from string import Template


class TextComponent:
    def __init__(self, text, x, y, size=1):
        """
        Text component
        Args:
            text: The test to be displayed
            x: The starting x coordinate, (0 is leftmost position)
            y: The starting y coordinate, (0 is highest position)
            size: The size of the text, from 1-3, (see the Adafruit GFX library documentation)
        """

        # Values we want the update method to apply a template to
        self._updatable_values = {"text": text, "x": x, "y": y, "size": size}

        # Copy the argument keys and values to self, allowing us to access them as attributes
        for key, value in self._updatable_values.iteritems():
            self.__dict__[key] = value

    def update(self, command_output):
        """
        Applies a template to each updatable attribute, (anything in _updatable_values)
        Args:
            command_output: A dict containing variable names and values, i.e. $var would be templated by {"var": 1}
        """
        logger.debug("Updating text component...")
        for key, value in self._updatable_values.iteritems():
            interpolated_value = Template(str(value)).safe_substitute(command_output)
            self.__dict__[key] = interpolated_value
