# -*- coding: utf-8 -*-
"""
BargraphComponent
Describes a value that can be displayed on a bargraph
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

from logzero import logger
from string import Template


class BargraphComponent:
    def __init__(self, value, green_threshold=0, yellow_threshold=50, red_threshold=75):
        """
        Bargraph component
        Args:
            value: The value to be drawn on the bargraph.  Can be a number from 0-100, or a $variable
            green_threshold: Any value larger than this will be green
            yellow_threshold: Any value larger than this will be yellow
            red_threshold: Any value larger than this will be red
        """

        self.BARGRAPH_LENGTH = 24

        # The graph string
        self.bargraph_data = ""

        # Values we want the update method to apply a template to
        self._updatable_values = {"value": value,
                                  "green_threshold": green_threshold,
                                  "yellow_threshold": yellow_threshold,
                                  "red_threshold": red_threshold}

        # Copy the argument keys and values to self, allowing us to access them as attributes
        for key, value in self._updatable_values.iteritems():
            self.__dict__[key] = value

    def update(self, command_output):
        """
        Applies a template to each updatable attribute, (anything in _updatable_values)
        Args:
            command_output: A dict containing variable names and values, i.e. $var would be templated by {"var": 1}
        """
        logger.debug("Updating bargraph component...")
        for key, value in self._updatable_values.iteritems():
            # Apply the template, (i.e. look for values with the '$var' syntax and replace)
            # See https://docs.python.org/2.4/lib/node109.html
            interpolated_value = Template(str(value)).safe_substitute(command_output)
            self.__dict__[key] = interpolated_value

        interpolated_graph_value = Template(self.value).safe_substitute(command_output)
        self.bargraph_data = self._percent_to_bargraph(interpolated_graph_value,
                                                       self.green_threshold,
                                                       self.yellow_threshold,
                                                       self.red_threshold)

    def get_as_dict(self):
        """ Returns attributes as dictionary """
        return {"bargraph_data": self.bargraph_data}

    def _percent_to_bargraph(self, value, green_threshold, yellow_threshold, red_threshold):
        """
        Convert an numeric argument between 0 and 100 to a string parsable by the microcontroller
        Args:
            value: The value to be drawn on the bargraph.  Can be a number from 0-100, or a $variable
            green_threshold: Any value larger than this will be green
            yellow_threshold: Any value larger than this will be yellow
            red_threshold: Any value larger than this will be red
        """

        # Create the initial list
        bargraph_data = ["o"] * self.BARGRAPH_LENGTH

        for i in xrange(0, len(bargraph_data)):
            if int(float(value)) > ((i + 1) * (100.0 / self.BARGRAPH_LENGTH)):
                if (i + 1) * (100.0 / self.BARGRAPH_LENGTH) >= int(red_threshold):
                    bargraph_data[i] = 'r'
                elif (i + 1) * (100.0 / self.BARGRAPH_LENGTH) >= int(yellow_threshold):
                    bargraph_data[i] = 'y'
                elif (i + 1) * (100.0 / self.BARGRAPH_LENGTH) >= int(green_threshold):
                    bargraph_data[i] = 'g'
                else:
                    bargraph_data[i] = 'o'

        return "".join(reversed(bargraph_data))
